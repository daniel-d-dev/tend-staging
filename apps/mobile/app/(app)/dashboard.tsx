import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { deleteToken } from "@/utils/token";

export default function DashboardScreen() {
    const router = useRouter();

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
            </TouchableOpacity>

            <TouchableOpacity
                style = {styles.button}
                onPress = {() => router.push("/(app)/temperature")}
            >
                <Text style = {styles.buttonText}>Temperature Check</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress = {async () => {await deleteToken(); router.replace("/(auth)/login"); }}>
                <Text>Logout</Text> {/* temporary logout button for testing which will be removed before pilot */}
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
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 16,
    }
});