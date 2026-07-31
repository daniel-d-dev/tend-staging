import { useState, useCallback } from "react";
import { useFocusEffect } from "expo-router";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function TemperatureScreen() {
    const [groups, setGroups] = useState<any[]>([]);
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [word, setWord] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [myWords, setMyWords] = useState<Record<number, string>>({});
    const [groupResult, setGroupResult] = useState<any>(null);

    const fetchGroups = useCallback(async () => {
        const token = await getToken();
        const groupsResponse = await fetch(`${API_URL}/groups/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (groupsResponse.ok) {
            const data = await groupsResponse.json();
            setGroups(data);
        }
        const wordsResponse = await fetch(`${API_URL}/temperature/mine`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (wordsResponse.ok) {
            const data = await wordsResponse.json();
            const map: Record<number, string> = {};
            data.forEach((check: any) => { map[check.group_id] = check.word; }); // convert to a map so words can be looked up by group id
            setMyWords(map);
        }
    }, []);

    const fetchGroupResult = async (groupId: number) => {
        const token = await getToken();
        const response = await fetch(`${API_URL}/temperature/group/${groupId}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            setGroupResult(data);
        }
    };

    useFocusEffect(useCallback(() => { fetchGroups(); }, [fetchGroups])); // useFocusEffect doesn't accept async functions, so fetchGroups is wrapped here

    const handleSubmit = async () => {
        if (!selectedGroup) {
            Alert.alert("Required", "Please select a group.");
            return;
        }

        const trimmed = word.trim();
        if (!trimmed || trimmed.includes(" ")) {
            Alert.alert("Invalid", "Please enter a single word.");
            return;
        }

        setSubmitting(true);
        const token = await getToken();
        const response = await fetch(`${API_URL}/temperature/`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ group_id: selectedGroup.id, word: trimmed })
        });
        setSubmitting(false);

        if (response.ok) {
            Alert.alert("Done", "Your word has been submitted.");
            setWord("");
            fetchGroups();
            fetchGroupResult(selectedGroup.id);
        } else {
            let message = "Something went wrong. Please try again";
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
            <ScrollView>
                <Text style = {styles.heading}>Weekly temperature check</Text>
                <Text style = {styles.label}>Select a group</Text>
                {groups.map(group => (
                    <TouchableOpacity
                        key = {group.id}
                        style = {(() => {
                            if (selectedGroup && selectedGroup.id === group.id) return [styles.groupCard, styles.groupCardSelected];
                            return styles.groupCard;
                        })()}
                        onPress = {() => { setSelectedGroup(group); setGroupResult(null); fetchGroupResult(group.id); }}
                    >
                        <Text style = {styles.groupName}>{group.name}</Text>
                        {myWords[group.id] !== undefined && (
                            <Text style = {styles.wordText}>Your word this week: {myWords[group.id]}</Text>
                        )}
                    </TouchableOpacity>
                ))}
                {selectedGroup && !myWords[selectedGroup.id] &&(
                    <View>
                        <Text style = {styles.label}>In one word, how has the group been feeling this week?</Text>
                        <TextInput
                            style = {styles.input}
                            placeholder = "e.g. hopeful"
                            value = {word}
                            onChangeText = {setWord}
                            autoCapitalize = "none"
                        />
                    </View>
                )}
                {selectedGroup && !myWords[selectedGroup.id] && (
                    <TouchableOpacity
                        style = {styles.button}
                        onPress = {handleSubmit}
                        disabled = {submitting}
                    >
                        <Text style = {styles.buttonText}>
                            {(() => {
                                if (submitting) return "Submitting...";
                                return "Submit";
                            })()}
                        </Text>
                    </TouchableOpacity>
                )}
                {selectedGroup && groupResult && (
                    <View style = {styles.resultsContainer}>
                        {(() => {
                            if (groupResult.revealed) {
                                return (
                                    <View>
                                        <Text style = {styles.resultsHeading}>This week's words</Text>
                                        <Text style = {styles.resultsText}>
                                            {Object.entries(groupResult.words as Record<string, number>)
                                                .sort((a, b) => b[1] - a[1])
                                                .map(([w, count]) => `${w} (${count})`)
                                                .join(" · ")}
                                        </Text>
                                    </View>
                                );
                            }
                            return <Text style = {styles.waiting}>Waiting for more responses ({groupResult.response_count} so far)</Text>;
                        })()}
                    </View>
                )}
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 24
    },
    heading: {
        fontSize: 22,
        fontWeight: "600",
        marginBottom: 24
    },
    label: {
        fontSize: 14,
        fontWeight: "500",
        marginBottom: 6,
        marginTop: 16
    },
    input: {
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 12,
        fontSize: 15
    },
    groupCard: {
        padding: 12,
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        marginBottom: 8
    },
    groupCardSelected: {
        borderColor: "#000",
        backgroundColor: "#f0f0f0"
    },
    groupName: {
        fontSize: 15
    },
    button: {
        marginTop: 32,
        backgroundColor: "#000",
        padding: 16,
        borderRadius: 8,
        alignItems: "center"
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 16
    },
    wordText: {
        fontSize: 13,
        color: "#888",
        marginTop: 4
    },
    resultsContainer: {
        marginTop: 24,
        padding: 16,
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8
    },
    resultsHeading: {
        fontSize: 15,
        fontWeight: "600",
        marginBottom: 8
    },
    resultsText: {
        fontSize: 14,
        color: "#444"
    },
    waiting: {
        fontSize: 14,
        color: "#888",
        fontStyle: "italic"
    }
});