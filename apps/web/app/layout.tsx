import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tend",
  description: "Peer support for friend groups",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}