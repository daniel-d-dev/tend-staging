"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function DashboardPage() {
    const router = useRouter();
    const [unreadCount, setUnreadCount] = useState(0);

    useEffect(() => {
        async function fetchUnreadCount() {
            const response = await fetch(`${API_URL}/notifications/me`, {
                credentials: "include"
            });
            if (response.ok) {
                const data = await response.json();
                setUnreadCount(data.filter((n: any) => !n.is_read).length);
            }
        }
        fetchUnreadCount();
    }, []);

    async function handleLogout() {
        await fetch(`${API_URL}/auth/logout`, {
            method: "POST",
            credentials: "include"
        });
        router.push("/login");
    }

    return (
        <div className={styles.container}>
            <div className={styles.headerRow}>
                <h1 className={styles.heading}>Dashboard</h1>
                <button className={styles.logout} onClick={handleLogout}>Log out</button>
            </div>
            <div className={styles.grid}>
                <Link href="/dashboard/checkin" className={styles.card}>
                    <h2 className={styles.cardTitle}>Check in</h2>
                    <p className={styles.cardDescription}>Record how you are feeling today</p>
                </Link>
                <Link href="/dashboard/groups" className={styles.card}>
                    <h2 className={styles.cardTitle}>Groups</h2>
                    <p className={styles.cardDescription}>Manage your friend groups</p>
                </Link>
                <Link href="/dashboard/notifications" className={styles.card}>
                    <h2 className={styles.cardTitle}>
                        Notifications
                        {unreadCount > 0 && <span className={styles.badge}>{unreadCount}</span>}
                    </h2>
                    <p className={styles.cardDescription}>See nudges about your friends</p>
                </Link>
                <Link href="/dashboard/temperature" className={styles.card}>
                    <h2 className={styles.cardTitle}>Temperature Check</h2>
                    <p className={styles.cardDescription}>Share a word for how your group's feeling this week</p>
                </Link>
            </div>
        </div>
    );
}