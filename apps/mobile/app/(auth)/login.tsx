import { View, Text, StyleSheet } from "react-native";

export default function LoginScreen() {
    return (
        <View style = {styles.container}>
            <Text>Login</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center"
    },
});