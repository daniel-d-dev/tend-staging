import { useState, useCallback } from "react";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { View, Text, TouchableOpacity, ScrollView, StyleSheet, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function GroupDetailScreen() {
    const { id, name } = useLocalSearchParams<{ id: string; name: string }>(); // passed as a query param when navigating from the groups list
    const router = useRouter();
    const [members, setMembers] = useState<any[]>([]);

    const fetchMembers = async () => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/groups/${id}/members`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            setMembers(data);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchMembers();
        }, [])
    );

    const handleAssignFriend = async (friendId: number, friendName: string) => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/groups/${id}/friend?friend_id=${friendId}`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            Alert.alert("Friend assigned", `${friendName} is now your designated friend in this group.`);
        } else {
            let message = "Could not assign friend. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            Alert.alert("Error", message);
        }
    };

    return (
        <SafeAreaView style = {styles.container}>
            <ScrollView contentContainerStyle = {styles.scroll}>
                <TouchableOpacity onPress = {() => router.back()}>
                    <Text style = {styles.back}>Back</Text>
                </TouchableOpacity>
                <Text style = {styles.heading}>{name}</Text>
                <Text style = {styles.sectionHeading}>Members</Text>
                {members.length === 0 && (
                    <Text style = {styles.empty}>No other members yet.</Text>
                )}
                {members.map(member => (
                    <View key = {member.user_id} style = {styles.memberRow}>
                        <Text style = {styles.memberName}>{member.first_name}</Text>
                        <TouchableOpacity
                            style = {styles.button}
                            onPress = {() => handleAssignFriend(member.user_id, member.first_name)}
                        >
                            <Text style = {styles.buttonText}>Set as friend</Text>
                        </TouchableOpacity>
                    </View>
                ))}
                <TouchableOpacity
                    style = {styles.button}
                    onPress = {() => router.push({ pathname: "/(app)/groups/feed", params: { group_id: id, name: name } })}
                >
                    <Text style = {styles.buttonText}>Group feed</Text>
                </TouchableOpacity>
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scroll: {
        padding: 24,
        paddingBottom: 48,
    },
    back: {
        fontSize: 15,
        marginBottom: 16,
    },
    heading: {
        fontSize: 22,
        fontWeight: "600",
        marginBottom: 24,
    },
    sectionHeading: {
        fontSize: 16,
        fontWeight: "600",
        marginBottom: 12,
    },
    empty: {
        color: "#888",
    },
    memberRow: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: "#eee",
    },
    memberName: {
        fontSize: 15,
    },
    button: {
        backgroundColor: "#000",
        paddingVertical: 8,
        paddingHorizontal: 14,
        borderRadius: 8,
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 14,
    },
});