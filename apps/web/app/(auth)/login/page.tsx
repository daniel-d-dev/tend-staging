"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/auth";
import styles from "./page.module.css";
import Link from "next/link";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    async function handleLogin() {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
                credentials: "include"
            });
            if (!response.ok) {
                let message = "Incorrect email or password";
                try {
                    const errorData = await response.json();
                    if (errorData.detail) message = errorData.detail;
                } catch {
                    // response body wasn't valid JSON, fall back to the generic message above
                }
                alert(message);
                return;
            }
            router.push("/dashboard");
        } catch {
            alert("Could not connect to the server.");
        }
    }

    return (
        <div className = {styles.container}>
            <h1 className = {styles.title}>Welcome back</h1>
            <input className = {styles.input}
                type = "email"
                placeholder = "Email"
                value = {email}
                onChange = {(e) => setEmail(e.target.value)}
            />
            <input className = {styles.input}
                type = "password"
                placeholder = "Password"
                value = {password}
                onChange = {(e) => setPassword(e.target.value)}
            />
            <button className = {styles.button} onClick = {handleLogin}>Log in</button>
            <p className = {styles.paragraph}>No account? <Link href = "/register" className = {styles.link}>Register here</Link></p>
        </div>
    );
}