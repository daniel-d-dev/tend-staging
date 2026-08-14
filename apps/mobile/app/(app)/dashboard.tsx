import { useState, useCallback } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { deleteToken, getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function DashboardScreen() {
    const router = useRouter();
    const [unreadCount, setUnreadCount] = useState(0);

    useFocusEffect(
        useCallback(() => {
            async function fetchUnreadCount() {
                const token = await getToken();
                const response = await fetch(`${API_URL}/notifications/me`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setUnreadCount(data.filter((n: any) => !n.is_read).length);
                }
            }
            fetchUnreadCount();
        }, [])
    );

    return (
        <View style = {styles.container}>
            <Text>Dashboard</Text>
            <TouchableOpacity
                style = {styles.button}
                onPress = {() => router.push("/(app)/checkin")}
            >
                <Text style = {styles.buttonText}>Check in</Text>
            </TouchableOpacity>

            <TouchableOpacity
                style = {styles.button}
                onPress = {() => router.push("/(app)/groups")}
            >
                <Text style = {styles.buttonText}>Groups</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
                style = {styles.button}
                onPress = {() => router.push("/(app)/notifications")}
            >
                <Text style = {styles.buttonText}>Notifications</Text>
                {unreadCount > 0 && (
                    <View style = {styles.badge}>
                        <Text style = {styles.badgeText}>{unreadCount}</Text>
                    </View>
                )}
            </TouchableOpacity>

            <TouchableOpacity
                style = {styles.button}
                onPress = {() => router.push("/(app)/temperature")}
            >
                <Text style = {styles.buttonText}>Temperature Check</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress = {async () => {await deleteToken(); router.replace("/(auth)/login"); }}>
                {/* temporary logout button for testing which will be removed before pilot */}
                <Text>Logout</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center"
    },
    button: {
        marginTop: 24,
        backgroundColor: "#000",
        padding: 16,
        borderRadius: 8,
        alignItems: "center",
        width: "80%",
        position: "relative",
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 16,
    },
    badge: {
        position: "absolute",
        top: -6,
        right: -6,
        backgroundColor: "#e0245e",
        borderRadius: 999,
        minWidth: 20,
        height: 20,
        alignItems: "center",
        justifyContent: "center",
        paddingHorizontal: 5,
    },
    badgeText: {
        color: "#fff",
        fontSize: 12,
        fontWeight: "700",
    }
});