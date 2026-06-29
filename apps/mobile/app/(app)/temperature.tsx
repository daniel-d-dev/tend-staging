import { useState, useCallback } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

export default function TemperatureScreen() {
    const router = useRouter();
    const [groups, setGroups] = useState<any[]>([]);
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [rating, setRating] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [myRatings, setMyRatings] = useState<Record<number, number>>({});

    const fetchGroups = useCallback(async () => {
        const token = await getToken();
        const groupsResponse = await fetch(`${API_URL}/groups/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (groupsResponse.ok) {
            const data = await groupsResponse.json();
            setGroups(data);
        }
        const ratingsResponse = await fetch(`${API_URL}/temperature/mine`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (ratingsResponse.ok) {
            const data = await ratingsResponse.json();
            const map: Record<number, number> = {};
            data.forEach((check: any) => { map[check.group_id] = check.rating; }); // convert to a map so ratings can be looked up by group id
            setMyRatings(map);
        }
    }, []);

    useFocusEffect(useCallback(() => { fetchGroups(); }, [fetchGroups])); // useFocusEffect doesn't accept async functions, so fetchGroups is wrapped here

    const handleSubmit = async () => {
        if (!selectedGroup) {
            Alert.alert("Required", "Please select a group.");
            return;
        }

        const ratingValue = parseInt(rating);
        if (ratingValue < 1 || ratingValue > 5) {
            Alert.alert("Invalid", "Rating must be between 1 and 5.");
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
            body: JSON.stringify({ group_id: selectedGroup.id, rating: ratingValue }) // ratingValue is parsedint version of rating
        });
        setSubmitting(false);

        if (response.ok) {
            Alert.alert("Done", "Your rating has been submitted.");
            setSelectedGroup(null);
            setRating("");
            fetchGroups();
        } else if (response.status === 400) {
            Alert.alert("Already submitted", "You have already rated this group this week.");
        } else {
            Alert.alert("Error", "Something went wrong. Please try again");
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
                        onPress = {() => setSelectedGroup(group)}
                    >
                        <Text style = {styles.groupName}>{group.name}</Text>
                        {myRatings[group.id] !== undefined && (
                            <Text style = {styles.ratingText}>Your rating this week: {myRatings[group.id]}/5</Text>
                        )}
                    </TouchableOpacity>
                ))}
                {selectedGroup && (
                    <View>
                        <Text style = {styles.label}>How has the group been feeling this week? (1-5)</Text>
                        <TextInput
                            style = {styles.input}
                            placeholder = "1 = low, 5 = great"
                            value = {rating}
                            onChangeText = {setRating}
                            keyboardType = "number-pad"
                        />
                    </View>
                )}
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
    ratingText: {
        fontSize: 13,
        color: "#888",
        marginTop: 4
    }
});