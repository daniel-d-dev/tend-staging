import { useState, useCallback } from "react";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function GroupDetailScreen() {
    const { id, name, createdBy } = useLocalSearchParams<{ id: string; name: string; createdBy: string }>(); // passed as query params when navigating from the groups list
    const router = useRouter();
    const [members, setMembers] = useState<any[]>([]);
    const [groupName, setGroupName] = useState(name);
    const [editingName, setEditingName] = useState(false);
    const [savingName, setSavingName] = useState(false);
    const [isCreator, setIsCreator] = useState(false);

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

    const checkIsCreator = async () => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            const me = await response.json();
            setIsCreator(String(me.id) === createdBy);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchMembers();
            checkIsCreator();
        }, [])
    );

    const handleRename = async () => {
        if (!groupName.trim()) {
            Alert.alert("Required", "Group name can't be empty.");
            return;
        }
        setSavingName(true);
        const token = await getToken();
        const response = await fetch(`${API_URL}/groups/${id}`, {
            method: "PATCH",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name: groupName.trim() })
        });
        setSavingName(false);
        if (response.ok) {
            setEditingName(false);
        } else {
            let message = "Could not rename group. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            Alert.alert("Error", message);
        }
    };

    const handleDelete = () => {
        Alert.alert(
            "Delete group",
            `Are you sure you want to delete "${groupName}"? This can't be undone.`,
            [
                { text: "Cancel", style: "cancel" },
                {
                    text: "Delete",
                    style: "destructive",
                    onPress: async () => {
                        const token = await getToken();
                        const response = await fetch(`${API_URL}/groups/${id}`, {
                            method: "DELETE",
                            headers: { Authorization: `Bearer ${token}` }
                        });
                        if (response.ok) {
                            router.replace("/(app)/groups");
                        } else {
                            Alert.alert("Error", "Could not delete group. Please try again.");
                        }
                    }
                }
            ]
        );
    };

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
                {editingName ? (
                    <View style = {styles.renameRow}>
                        <TextInput
                            style = {styles.renameInput}
                            value = {groupName}
                            onChangeText = {setGroupName}
                            autoFocus
                        />
                        <TouchableOpacity style = {styles.button} onPress = {handleRename} disabled = {savingName}>
                            <Text style = {styles.buttonText}>{savingName ? "Saving..." : "Save"}</Text>
                        </TouchableOpacity>
                    </View>
                ) : (
                    <View style = {styles.renameRow}>
                        <Text style = {styles.heading}>{groupName}</Text>
                        {isCreator && (
                            <TouchableOpacity onPress = {() => setEditingName(true)}>
                                <Text style = {styles.editLink}>Rename</Text>
                            </TouchableOpacity>
                        )}
                    </View>
                )}
                {isCreator && (
                    <TouchableOpacity onPress = {handleDelete}>
                        <Text style = {styles.deleteLink}>Delete group</Text>
                    </TouchableOpacity>
                )}
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
    },
    renameRow: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 8,
        gap: 12,
    },
    renameInput: {
        flex: 1,
        fontSize: 22,
        fontWeight: "600",
        borderBottomWidth: 1,
        borderBottomColor: "#ccc",
        paddingVertical: 4,
    },
    editLink: {
        fontSize: 13,
        color: "#555",
    },
    deleteLink: {
        fontSize: 13,
        color: "#c0392b",
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