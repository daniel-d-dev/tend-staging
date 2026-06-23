import { useState, useCallback } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";
import { Audio } from "expo-av";

export default function CheckInScreen() {
    const router = useRouter();
    const [existing, setExisting] = useState(null);
    const [promptQuestion, setPromptQuestion] = useState("");
    const [promptResponse, setPromptResponse] = useState("");
    const [journalText, setJournalText] = useState("");
    const [sleepHours, setSleepHours] = useState("");
    const [stepCount, setStepCount] = useState("");
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [activeRecording, setActiveRecording] = useState<Audio.Recording | null>(null);
    const [recordingField, setRecordingField] = useState<"prompt" | "journal" | null>(null);
    const [transcribing, setTranscribing] = useState(false);

    useFocusEffect(
        useCallback(() => {
            const fetchToday = async () => {
                const token = await getToken();
                let response = await fetch(`${API_URL}/checkins/today`, {
                    headers: { Authorization: `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    setExisting(data);
                    setPromptQuestion(data.prompt_question);
                    setPromptResponse(data.prompt_response);
                    if (data.journal_text) setJournalText(data.journal_text);
                    if (data.sleep_hours) setSleepHours(data.sleep_hours.toString());
                    if (data.step_count) setStepCount(data.step_count.toString());
                } else { // if there's been no check in today, fetch today's prompt instead
                    response = await fetch(`${API_URL}/checkins/prompt/today`, {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    if (response.ok) {
                        const data = await response.json();
                        setPromptQuestion(data.prompt);
                    }
                }

                setLoading(false);
            };

            fetchToday();
        }, [])
    );

    const handleSubmit = async () => {
        if (!promptResponse.trim()) {
            Alert.alert("Required", "Please respond to the prompt before submitting.");
            return
        }

        setSubmitting(true)

        const token = await getToken();

        let method = "POST";
        let url = `${API_URL}/checkins/`

        if (existing) {
            method = "PATCH";
            url = `${API_URL}/checkins/today`
        }

        const body: any = {
            prompt_question: promptQuestion,
            prompt_response: promptResponse.trim(),
            journal_text: journalText.trim() || null,
            sleep_hours: null,
            step_count: null,
        };

        if (sleepHours) body.sleep_hours = parseFloat(sleepHours);
        if (stepCount) body.step_count = parseInt(stepCount);

        if (method === "PATCH") {
            delete body.prompt_question; // CheckInUpdate doesn't include this field
        }

        const response = await fetch(url, {
            method,
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        setSubmitting(false);

        if (response.ok) {
            router.replace("/(app)/dashboard");
        } else {
            Alert.alert("Error", "Something went wrong. Please try again.")
        }
    };

    const handleStartRecording = async (field: "prompt" | "journal") => {
        try {
            const { status } = await Audio.requestPermissionsAsync();
            if (status !== "granted") {
                Alert.alert("Permission required", "Microphone access is required to record audio.");
                return;
            }
            await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true }) // android handles this automatically
            const { recording } = await Audio.Recording.createAsync(
                Audio.RecordingOptionsPresets.HIGH_QUALITY
            );
            setActiveRecording(recording);
            setRecordingField(field);
        } catch {
            Alert.alert("Error", "Could not start recording. Please try again.")
        }
    };

    const handleStopRecording = async () => {
        if (!activeRecording || !recordingField) return;
        const field = recordingField; // recordingField gets set to null in the finally block so its captured here first
        try {
            await activeRecording.stopAndUnloadAsync();
            const uri = activeRecording.getURI();
            setActiveRecording(null);
            if (!uri) {
                setRecordingField(null)
                return;
            }
            setTranscribing(true)
            const token = await getToken();
            const formData = new FormData();
            formData.append("audio", { uri, name: "audio.m4a", type: "audio/m4a" } as any); // audio can't be sent as JSON so we use FormData. 'as any' is needed because typescript doesnt recognise the react native file format
            const response = await fetch(`${API_URL}/checkins/note/transcribe`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData
            });
            if (response.ok) {
                const data = await response.json();
                if (field === "prompt") {
                    setPromptResponse(data.transcript);
                } else {
                    setJournalText(data.transcript);
                }
            } else {
                Alert.alert("Error", "Could not transcribe audio. Please try again.");
            }
        } catch {
            Alert.alert("Error", "Something went wrong. Please try again.");
        } finally {
            setTranscribing(false);
            setRecordingField(null);
        }
    };

    if (loading) {
        return (
            <View style = {styles.container}>
                <Text>Loading...</Text>
            </View>
        );
    }

    return (
        <KeyboardAvoidingView
            style = {styles.flex}
            behavior = {Platform.OS === "ios" ? "padding" : "height"}
        >
            <SafeAreaView style = {styles.safeArea}>
                <ScrollView contentContainerStyle = {styles.container}>
                    <Text style = {styles.prompt}>{promptQuestion}</Text>
                    <TextInput
                        style = {styles.textArea}
                        placeholder = "Your response..."
                        value = {promptResponse}
                        onChangeText = {setPromptResponse}
                        multiline
                    />
                    <TouchableOpacity
                        style = {styles.micButton}
                        onPress = {() => recordingField === "prompt" ? handleStopRecording() : handleStartRecording("prompt")}
                        disabled = {transcribing || (recordingField !== null && recordingField !== "prompt")}
                    >
                        <Text style = {styles.micButtonText}>
                            {(() => {
                                if (recordingField === "prompt" && !transcribing) return "Stop recording";
                                if (recordingField === "prompt" && transcribing) return "Transcribing...";
                                return "Record";
                            })()}
                        </Text>
                    </TouchableOpacity>
                    <Text style = {styles.label}>Anything else on your mind?</Text>
                    <TextInput
                        style = {styles.textArea}
                        placeholder = "Optional..."
                        value = {journalText}
                        onChangeText = {setJournalText}
                        multiline
                    />
                    <TouchableOpacity
                        style = {styles.micButton}
                        onPress = {() => recordingField === "journal" ? handleStopRecording() : handleStartRecording("prompt")}
                        disabled = {transcribing || (recordingField !== null && recordingField !== "journal")}
                    >
                        <Text style = {styles.micButtonText}>
                            {(() => {
                                if (recordingField === "prompt" && !transcribing) return "Stop recording";
                                if (recordingField === "prompt" && transcribing) return "Transcribing...";
                                return "Record";
                            })()}
                        </Text>
                    </TouchableOpacity>
                    <Text style = {styles.label}>Sleep last night in hours</Text>
                    <TextInput
                        style = {styles.input}
                        placeholder = "e.g. 7.5"
                        value = {sleepHours}
                        onChangeText = {setSleepHours}
                        keyboardType = "decimal-pad"
                    />
                    <Text style = {styles.label}>Steps today, rounded to the nearest thousand</Text>
                    <TextInput
                        style = {styles.input}
                        placeholder = "e.g. 8000"
                        value = {stepCount}
                        onChangeText = {setStepCount}
                        keyboardType = "number-pad"
                    />
                    <TouchableOpacity
                        style = {styles.button}
                        onPress = {handleSubmit}
                        disabled = {submitting}
                    >
                        <Text style = {styles.buttonText}>
                            {(() => {
                                if (submitting) return "Saving...";
                                if (existing) return "Update";
                                return "Submit"
                            })()}
                        </Text>
                    </TouchableOpacity>
                </ScrollView>
            </SafeAreaView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    flex: {
        flex: 1
    },
    safeArea: {
        flex: 1
    },
    container: {
        padding: 24,
        paddingBottom: 48
    },
    prompt: {
        fontSize: 18,
        fontWeight: "600",
        marginBottom: 12,
    },
    label: {
        fontSize: 14,
        fontWeight: "500",
        marginTop: 20,
        marginBottom: 6,
    },
    textArea: {
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 12,
        fontSize: 15,
        minHeight: 100,
        textAlignVertical: "top",
    },
    input: {
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 12,
        fontSize: 15,
    },
    button: {
        marginTop: 32,
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
    micButton: {
        alignSelf: "flex-start",
        marginTop: 8,
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 6,
    },
    micButtonText: {
        fontSize: 13,
        color: "#555",
    },
});