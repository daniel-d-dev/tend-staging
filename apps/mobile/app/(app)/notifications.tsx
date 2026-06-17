import { useState, useCallback } from "react";
import { useFocusEffect } from "expo-router";
import { Text, TouchableOpacity, ScrollView, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function NotificationsScreen() {
    const [notifications, setNotifications] = useState<any[]>([]);

    const fetchNotifications = async () => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/notifications/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            setNotifications(data);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchNotifications();
        }, [])
    );

    const handleMarkAsRead = async (id: number) => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/notifications/${id}/read`, {
            method: "PATCH",
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            fetchNotifications();
        }
    };

    return (
            <SafeAreaView style = {styles.container}>
                <ScrollView contentContainerStyle = {styles.scroll}>
                    <Text style = {styles.heading}>Notifications</Text>

                    {notifications.length === 0 && (
                        <Text style = {styles.empty}>No notifications yet.</Text>
                    )}

                    {notifications.map(notification => (
                        <TouchableOpacity
                            key = {notification.id}
                            style = {[styles.card, notification.is_read && styles.cardRead]}
                            onPress = {() => handleMarkAsRead(notification.id)}
                        >
                            <Text style = {styles.message}>{notification.message}</Text>
                            <Text style = {styles.date}>
                                {new Date(notification.created_at).toLocaleDateString()}
                            </Text>
                            {!notification.is_read && (
                                <Text style = {styles.unread}>Tap to mark as read</Text>
                            )}
                        </TouchableOpacity>
                    ))}
                </ScrollView>
            </SafeAreaView>
        );
    };

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scroll: {
        padding: 24,
        paddingBottom: 48,
    },
    heading: {
        fontSize: 22,
        fontWeight: "600",
        marginBottom: 16,
    },
    empty: {
        color: "#888",
    },
    card: {
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
    },
    cardRead: {
        opacity: 0.5,
    },
    message: {
        fontSize: 15,
        marginBottom: 6,
    },
    date: {
        fontSize: 12,
        color: "#888",
    },
    unread: {
        fontSize: 12,
        color: "#000",
        marginTop: 8,
        fontWeight: "600",
    },
});