"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/auth";
import styles from "./page.module.css";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    async function handleLogin() {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, display_name: "" }),
                credentials: "include"
            });
            if (!response.ok) {
                alert("Incorrect email or password");
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
            <p className = {styles.paragraph}>No account? <a href = "/register" className = {styles.link}>Register here</a></p>
        </div>
    );
}