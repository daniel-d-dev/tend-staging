import { useState } from "react";
import { Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard } from "react-native";
import { useRouter } from "expo-router";
import { API_URL } from "@/constants/api";

export default function RegisterScreen() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [firstName, setFirstName] = useState("");
    const [password, setPassword] = useState("");

    // call the register endpoint and navigate to login on success
    async function handleRegister() {
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, first_name: firstName })
            });
            if (!response.ok) {
                let message = "Please check your details and try again.";
                try {
                    const errorData = await response.json();
                    if (errorData.detail) message = errorData.detail;
                } catch {
                    // response body wasn't valid JSON, fall back to the generic message above
                }
                Alert.alert("Registration failed", message);
                return;
            }
            router.replace("/(auth)/login");
        } catch {
            Alert.alert("Error", "Could not connect to the server.");
        }
    }

    return (
        <TouchableWithoutFeedback onPress = {Keyboard.dismiss}>
            <KeyboardAvoidingView style = {styles.container} behavior = {Platform.OS === "ios" ? "padding" : "height"}>
                <Text style = {styles.title}>Create an account</Text>
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
                    placeholder = "First name"
                    value = {firstName}
                    onChangeText = {setFirstName}
                />
                <TextInput 
                    style = {styles.input}
                    placeholder = "Password"
                    value = {password}
                    onChangeText = {setPassword}
                    secureTextEntry
                />
                <TouchableOpacity style = {styles.button} onPress = {handleRegister}>
                    <Text style = {styles.buttonText}>Register</Text>
                </TouchableOpacity>
                <Text>Already have an account? <Text style = {styles.linkBold} onPress = {() => router.push("/(auth)/login")}>Log in here</Text></Text>
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