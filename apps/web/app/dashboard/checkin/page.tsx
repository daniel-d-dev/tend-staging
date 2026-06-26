"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function CheckInPage() {
    const router = useRouter();
    const [existing, setExisting] = useState(null);
    const [promptQuestion, setPromptQuestion] = useState("");
    const [promptResponse, setPromptResponse] = useState("");
    const [journalText, setJournalText] = useState("");
    const [sleepHours, setSleepHours] = useState("");
    const [stepCount, setStepCount] = useState("");
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [activeRecorder, setActiveRecorder] = useState<MediaRecorder | null>(null);
    const [recordingField, setRecordingField] = useState<"prompt" | "journal" | null>(null);
    const [transcribing, setTranscribing] = useState(false);
    const [audioEmotionScore, setAudioEmotionScore] = useState<number | null>(null);
    const audioPartsRef = useRef<BlobPart[]>([]); // MediaRecorder fires audio in parts, they are collected here and combined into one file on stop

    useEffect(() => {
        const fetchToday = async () => {
            let response = await fetch(`${API_URL}/checkins/today`, {
                credentials: "include"
            });

            if (response.ok) {
                const data = await response.json();
                setExisting(data);
                setPromptQuestion(data.prompt_question);
                setPromptResponse(data.prompt_response);
                if (data.journal_text) setJournalText(data.journal_text);
                if (data.sleep_hours) setSleepHours(data.sleep_hours.toString());
                if (data.step_count) setStepCount(data.step_count.toString());
            } else {
                // if there's been no check in today, fetch today's prompt instead
                response = await fetch(`${API_URL}/checkins/prompt/today`, {
                    credentials: "include"
                });
                if (response.ok) {
                    const data = await response.json();
                    setPromptQuestion(data.prompt)
                }
            }

            setLoading(false);
        };

        fetchToday();
    }, []);

    const handleSubmit = async () => {
        if (!promptResponse.trim()) {
            alert("Please respond to the prompt before submitting.");
            return;
        }

        setSubmitting(true)

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
            audio_emotion_score: audioEmotionScore
        };

        if (sleepHours) body.sleep_hours = parseFloat(sleepHours);
        if (stepCount) body.step_count = parseInt(stepCount);

        if (method === "PATCH") {
            delete body.prompt_question; // CheckInUpdate doesn't include this field
        }

        const response = await fetch(url, {
            method,
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
            body: JSON.stringify(body)
        });

        setSubmitting(false);

        if (response.ok) {
            router.replace("/dashboard");
        } else {
            alert("Something went wrong. Please try again.")
        }
    };

    const handleStartRecording = async (field: "prompt" | "journal") => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            audioPartsRef.current = []; // reset from any previous recording

            recorder.ondataavailable = (e) => {
                audioPartsRef.current.push(e.data);
            };

            recorder.onstop = async () => {
                const blob = new Blob(audioPartsRef.current, { type: "audio/webm" });
                stream.getTracks().forEach(track => track.stop()); // release the mic so the browser stops showing the recording sign
                setTranscribing(true);
                try {
                    const formData = new FormData();
                    formData.append("audio", blob, "audio.webm");
                    const response = await fetch(`${API_URL}/checkins/note/transcribe`, {
                        method: "POST",
                        credentials: "include",
                        body: formData
                    });
                    if (response.ok) {
                        const data = await response.json();
                        if (field === "prompt") {
                            setPromptResponse(data.transcript);
                        } else {
                            setJournalText(data.transcript);
                        }
                        if (data.audio_emotion !== null && data.audio_emotion !== undefined) {
                            setAudioEmotionScore(data.audio_emotion);
                        }
                    } else {
                        alert("Could not transcribe audio. Please try again.");
                    }
                } catch {
                    alert("Something went wrong. Please try again.");
                } finally {
                    setTranscribing(false);
                    setRecordingField(null);
                }
            };

            recorder.start();
            setActiveRecorder(recorder);
            setRecordingField(field);
        } catch {
            alert("Could not access microphone. Please check your permissions.");
        }
    };

    const handleStopRecording = () => {
        if (!activeRecorder) return;
        activeRecorder.stop();
        setActiveRecorder(null);
    };

    if (loading) {
        return <p> Loading...</p>
    }

    return (
        <main className = {styles.container}>
            <h1 className={styles.heading}>Check in</h1>
            <p className = {styles.prompt}>{promptQuestion}</p>

            <textarea
                className = {styles.textArea}
                placeholder = "Your response..."
                value = {promptResponse}
                onChange = {(e) => setPromptResponse(e.target.value)}
            />

            <button
                className = {styles.micButton}
                onClick = {() => recordingField === "prompt" ? handleStopRecording() : handleStartRecording("prompt")}
                disabled = {transcribing || (recordingField !== null && recordingField !== "prompt")}
                >
                    {(() => {
                        if (recordingField === "prompt" && !transcribing) return "Stop recording";
                        if (recordingField === "prompt" && transcribing) return "Transcribing...";
                        return "Record";
                    })()}
            </button>

            <label className = {styles.label}>Anything else on your mind?</label>
            <textarea
                className = {styles.textArea}
                placeholder = "Optional..."
                value = {journalText}
                onChange = {(e) => setJournalText(e.target.value)}
            />

            <button
                className = {styles.micButton}
                onClick = {() => recordingField === "journal" ? handleStopRecording() : handleStartRecording("journal")}
                disabled = {transcribing || (recordingField !== null && recordingField !== "journal")}
                >
                    {(() => {
                        if (recordingField === "journal" && !transcribing) return "Stop recording";
                        if (recordingField === "journal" && transcribing) return "Transcribing...";
                        return "Record";
                    })()}
            </button>

            <label className = {styles.label}>Sleep last night in hours</label>
            <input
                className = {styles.input}
                placeholder = "e.g. 7.5"
                value = {sleepHours}
                onChange = {(e) => setSleepHours(e.target.value)}
                type = "number"
                step = "0.5"
            />

            <label className = {styles.label}>Steps today, rounded to the nearest thousand</label>
            <input
                className = {styles.input}
                placeholder = "e.g. 8000"
                value = {stepCount}
                onChange = {(e) => setStepCount(e.target.value)}
                type = "number"
            />

            <button
                className = {styles.button}
                onClick = {handleSubmit}
                disabled = {submitting}
            >
                {(() => {
                    if (submitting) return "Saving...";
                    if (existing) return "Update";
                    return "Submit";
                })()}
            </button>
        </main>
    );
}