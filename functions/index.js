
const functions = require("firebase-functions");
const admin = require("firebase-admin");
const { Client, Environment } = require("square");
const cors = require("cors")({ origin: true });

admin.initializeApp();
const db = admin.firestore();

// IMPORTANT: You must set these in your Firebase environment
// firebase functions:config:set square.accesstoken="YOUR_TOKEN" square.locationid="YOUR_LOCATION_ID"
const squareClient = new Client({
  environment: Environment.Production,
  accessToken: functions.config().square.accesstoken,
});

exports.createCheckout = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError("unauthenticated", "You must be logged in to make a purchase.");
  }

  const { plan } = data;
  if (!plan || (plan !== "operative" && plan !== "godmode")) {
    throw new functions.https.HttpsError("invalid-argument", "Invalid plan specified.");
  }

  try {
    const response = await squareClient.checkoutApi.createPaymentLink({
      idempotencyKey: context.auth.uid + new Date().toISOString(),
      description: `SYNAPSE AI - ${plan.toUpperCase()} Plan`,
      order: {
        locationId: functions.config().square.locationid,
        lineItems: [
          {
            name: `${plan.toUpperCase()} Plan`,
            quantity: "1",
            basePriceMoney: {
              amount: plan === "operative" ? 1999 : 9999, // Price in cents
              currency: "USD",
            },
          },
        ],
      },
      checkoutOptions: {
        allowTipping: false,
        redirectUrl: `https://coaihq.online/success.html?session_id={CHECKOUT_ID}`,
        askForShippingAddress: false,
      },
      metadata: {
        userId: context.auth.uid,
        plan: plan,
      },
    });

    return { url: response.result.paymentLink.url };
  } catch (error) {
    console.error("Square API Error:", error);
    throw new functions.https.HttpsError("internal", "Could not create Square checkout link.", error);
  }
});

exports.squareWebhook = functions.https.onRequest(async (req, res) => {
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  // We will add signature verification later for security
  const { type, data } = req.body;

  if (type === "payment.updated") {
    const payment = data.object.payment;
    if (payment.status === "COMPLETED") {
      const orderId = payment.order_id;
      
      try {
        const order = await squareClient.ordersApi.retrieveOrder(orderId);
        const metadata = order.result.order.metadata;
        
        if (metadata && metadata.userId && metadata.plan) {
          const userId = metadata.userId;
          const plan = metadata.plan;

          await db.collection("users").doc(userId).update({
            plan: plan.toUpperCase(),
          });
          console.log(`Successfully upgraded user ${userId} to ${plan.toUpperCase()}`);
        }
      } catch (error) {
        console.error("Error processing webhook:", error);
      }
    }
  }

  return res.status(200).send("Received");
});
