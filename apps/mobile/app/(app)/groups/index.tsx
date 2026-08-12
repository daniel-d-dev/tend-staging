import { useState, useCallback } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function GroupsScreen() {
    const [groups, setGroups] = useState<any[]>([]); // no formal type yet, placeholder for now
    const [groupName, setGroupName] = useState("");
    const [joinCode, setJoinCode] = useState("");
    const [creating, setCreating] = useState(false)
    const [joining, setJoining] = useState(false)
    const router = useRouter();

    const fetchGroups = async () => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/groups/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            setGroups(data);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchGroups();
        }, [])
    );

    const handleCreateGroup = async () => {
        if (!groupName.trim()) {
            Alert.alert("Required", "Please enter a group name.");
            return;
        }
        setCreating(true)
        const token = await getToken();
        const response = await fetch(`${API_URL}/groups/`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name: groupName.trim() })
        });
        setCreating(false)
        if (response.ok) {
            setGroupName("");
            const data = await response.json()
            setGroups(prev => [...prev, data]);
        } else {
            let message = "Could not create group. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            Alert.alert("Error", message);
        }
    };

    const handleJoinGroup = async () => {
        if (!joinCode.trim()) {
            Alert.alert("Required", "Please enter a join code.");
            return;
        }
        setJoining(true)
        const token = await getToken();
        const response = await fetch(`${API_URL}/groups/join?join_code=${joinCode.trim().toUpperCase()}`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` }
        });
        setJoining(false)
        if (response.ok) {
            setJoinCode("");
            fetchGroups();
        } else {
            let message = "Could not join group. Please try again.";
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
                <Text style = {styles.heading}>My Groups</Text>

                {groups.length === 0 && (
                    <Text style = {styles.empty}>You are not in any groups yet.</Text>
                )}

                {groups.map(group => (
                    <TouchableOpacity
                        key = {group.id}
                        style = {styles.groupCard}
                        onPress = {() => router.push({ pathname: "/(app)/groups/[id]", params: { id: group.id, name: group.name, createdBy: group.created_by }
                })}
                    >
                        <Text style = {styles.groupName}>{group.name}</Text>
                        <Text style = {styles.joinCode}>Join code: {group.join_code}</Text>
                    </TouchableOpacity>
                ))}

                <Text style = {styles.sectionHeading}>Create a group</Text>
                <TextInput
                    style = {styles.input}
                    placeholder = "Group name"
                    value = {groupName}
                    onChangeText = {setGroupName}
                />
                <TouchableOpacity
                    style = {styles.button}
                    onPress = {handleCreateGroup}
                    disabled = {creating}
                >
                    <Text style = {styles.buttonText}>
                        {(() => {
                            if (creating) return "Creating...";
                            return "Create group";
                        })()}
                    </Text>
                </TouchableOpacity>

                <Text style = {styles.sectionHeading}>Join a group</Text>
                <TextInput
                    style = {styles.input}
                    placeholder = "Enter join code"
                    value = {joinCode}
                    onChangeText = {setJoinCode}
                    autoCapitalize = "characters"
                />
                <TouchableOpacity
                    style = {styles.button}
                    onPress = {handleJoinGroup}
                    disabled = {joining}
                >
                    <Text style = {styles.buttonText}>
                        {(() => {
                            if (joining) return "Joining...";
                            return "Join group";
                        })()}
                    </Text>
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
    heading: {
        fontSize: 22,
        fontWeight: "600",
        marginBottom: 16,
    },
    sectionHeading: {
        fontSize: 16,
        fontWeight: "600",
        marginTop: 32,
        marginBottom: 12,
    },
    empty: {
        color: "#888",
        marginBottom: 16,
    },
    groupCard: {
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
    },
    groupName: {
        fontSize: 16,
        fontWeight: "600",
        marginBottom: 4,
    },
    joinCode: {
        fontSize: 13,
        color: "#555",
    },
    input: {
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 12,
        fontSize: 15,
        marginBottom: 12,
    },
    button: {
        backgroundColor: "#000",
        padding: 16,
        borderRadius: 8,
        alignItems: "center",
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 16,
    },
});