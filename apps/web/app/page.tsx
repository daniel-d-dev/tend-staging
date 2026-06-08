import { redirect } from "next/navigation";
import { getMe } from "@/lib/auth";

export default async function Home() {
  const user = await getMe();
  if (user) redirect("/dashboard");
  redirect("/login");
}