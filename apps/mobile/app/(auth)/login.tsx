import { useState } from "react";
import { Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard } from "react-native";
import { useRouter } from "expo-router";
import { saveToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function LoginScreen() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // call the login endpoint, save the token and navigate into the app
    async function handleLogin() {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, display_name: "" })
            });
            if (!response.ok) {
                Alert.alert("Login failed", "Incorrect email or password.");
                return;
            }
            const data = await response.json();
            await saveToken(data.access_token);
            router.replace("/(app)/dashboard");
        } catch {
            Alert.alert("Error", "Could not connect to the server.");
        }
    }

    return (
        <TouchableWithoutFeedback onPress = {Keyboard.dismiss}>
            <KeyboardAvoidingView style = {styles.container} behavior = {Platform.OS === "ios" ? "padding" : "height"}>
                <Text style = {styles.title}>Welcome back</Text>
                <TextInput 
                    style = {styles.input}
                    placeholder = "Email"
                    value = {email}
                    onChangeText = {setEmail}
                    autoCapitalize = "none"
                    keyboardType = "email-address"
                />
                <TextInput 
                    style = {styles.input}
                    placeholder = "Password"
                    value = {password}
                    onChangeText = {setPassword}
                    secureTextEntry
                />
                <TouchableOpacity style = {styles.button} onPress = {handleLogin}>
                    <Text style = {styles.buttonText}>Log in</Text>
                </TouchableOpacity>
                <Text>No account? <Text style = {styles.linkBold} onPress = {() => router.push("/(auth)/register")}>Register here</Text>
                </Text>
            </KeyboardAvoidingView>
        </TouchableWithoutFeedback>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        backgroundColor: "#fff"
    },
    title: {
        fontSize: 24,
        fontWeight: "600",
        marginBottom: 32
    },
    input: {
        width: "100%",
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 12,
        marginBottom: 16,
        fontSize: 16
    },
    button: {
        width: "100%",
        backgroundColor: "#000",
        padding: 14,
        borderRadius: 8,
        alignItems: "center",
        marginBottom: 16
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 16
    },
    linkBold: {
        fontWeight: "600",
        textDecorationLine: "underline"
    }
});