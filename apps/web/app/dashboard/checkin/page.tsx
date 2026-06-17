"use client";

import { useState, useEffect } from "react";
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

    if (loading) {
        return <p> Loading...</p>
    }

    return (
        <main className = {styles.container}>
            <p className = {styles.prompt}>{promptQuestion}</p>

            <textarea
                className = {styles.textArea}
                placeholder = "Your response..."
                value = {promptResponse}
                onChange = {(e) => setPromptResponse(e.target.value)}
            />

            <label className = {styles.label}>Anything else on your mind?</label>
            <textarea
                className = {styles.textArea}
                placeholder = "Optional..."
                value = {journalText}
                onChange = {(e) => setJournalText(e.target.value)}
            />

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