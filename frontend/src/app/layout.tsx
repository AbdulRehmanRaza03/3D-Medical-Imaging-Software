import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "@/lib/providers";

export const metadata: Metadata = {
  title: "OrthoVision AI — Medical 3D Imaging",
  description:
    "Medical imaging research and visualization platform. Not a diagnostic device.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
