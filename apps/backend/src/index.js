import "dotenv/config";
import app from "./app.js";
import connectDB from "./db/index.js";

const port = process.env.PORT || 4000;

connectDB()
  .then(() => {
    app.listen(port, () => {
      console.log(`MedSync API running at http://localhost:${port}`);
    });
  })
  .catch((err) => {
    console.error("Server startup failed", err);
    process.exit(1);
  });
