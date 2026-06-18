import { Tabs } from "expo-router";
import { useEffect } from "react";
import * as Notifications from "expo-notifications";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

async function registerPushToken() {
    try {
        const { status } = await Notifications.requestPermissionsAsync();
        if (status !== "granted") return;

        const tokenData = await Notifications.getExpoPushTokenAsync();
        const pushToken = tokenData.data;

        const authToken = await getToken();
        await fetch(`${API_URL}/users/push-token`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${authToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ token: pushToken })
        });
    } catch (e) {
        // push token registration failed and the app continues as normal
    }
}

export default function AppLayout() {
    useEffect(() => {
        registerPushToken();
    }, []);

    return (
        <Tabs screenOptions = {{ headerShown: false }} />
    );
}