"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function NotificationsPage() {
    const [notifications, setNotifications] = useState<any[]>([]);

    const fetchNotifications = async () => {
        const response = await fetch(`${API_URL}/notifications/me`, {
            credentials: "include"
        });
        if (response.ok) {
            const data = await response.json();
            setNotifications(data);
        }
    };

    useEffect(() => {
        fetchNotifications();
    }, []);

    const handleMarkAsRead = async (id: number) => {
        const response = await fetch(`${API_URL}/notifications/${id}/read`, {
            method: "PATCH",
            credentials: "include"
        });
        if (response.ok) {
            fetchNotifications();
        }
    };

    return (
        <main className = {styles.container}>
            <h1 className = {styles.heading}>Notifications</h1>

            {notifications.length === 0 && (
                <p className = {styles.empty}>No notifications yet.</p>
            )}

            {notifications.map(notification => (
                <div
                    key = {notification.id}
                    className = {(() => {
                        if (notification.is_read) return `${styles.card} ${styles.cardRead}`;
                        return styles.card;
                    })()}
                >
                    <p className = {styles.message}>{notification.message}</p>
                    <p className = {styles.date}>
                        {new Date(notification.created_at).toLocaleDateString()}
                    </p>
                    {!notification.is_read && (
                        <button
                            className = {styles.readButton}
                            onClick = {() => handleMarkAsRead(notification.id)}
                        >
                            Mark as read
                        </button>
                    )}
                </div>
            ))}
        </main>
    );
}