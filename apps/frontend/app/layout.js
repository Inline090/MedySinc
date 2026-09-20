import "./globals.css";

import { Providers } from "./providers";

export const metadata = {
  title: "MedSync",
  description: "Upload medical documents and ask questions answered from your own records.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
