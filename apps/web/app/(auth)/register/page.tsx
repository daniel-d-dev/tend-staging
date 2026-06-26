"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/auth";
import styles from "./page.module.css"
import Link from "next/link";

export default function RegisterPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [firstName, setFirstName] = useState("");
    const [password, setPassword] = useState("");

    async function handleRegister() {
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, first_name: firstName })
            });
            if (!response.ok) {
                alert("Registration failed. Please check your details.");
                return;
            }
            router.push("/login");
        } catch {
            alert("Could not connect to the server.");
        }
    }

    return (
        <div className = {styles.container}>
            <h1 className = {styles.title}>Create an account</h1>
            <input className = {styles.input}
                type = "email"
                placeholder = "Email"
                value = {email}
                onChange = {(e) => setEmail(e.target.value)}
            />
            <input className = {styles.input}
                type = "text"
                placeholder = "First name"
                value = {firstName}
                onChange = {(e) => setFirstName(e.target.value)}
            />
            <input className = {styles.input}
                type = "password"
                placeholder = "Password"
                value = {password}
                onChange = {(e) => setPassword(e.target.value)}
            />
            <button className = {styles.button} onClick = {handleRegister}>Register</button>
            <p className = {styles.paragraph}>Already have an account? <Link href = "/login" className = {styles.link}>Log in here</Link></p>
        </div>
    );
}