import { View, Text, StyleSheet } from "react-native";

export default function RegisterScreen() {
    return (
        <View style = {styles.container}>
            <Text>Register</Text>
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