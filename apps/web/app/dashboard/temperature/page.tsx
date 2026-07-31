"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function TemperaturePage() {
    const router = useRouter();
    const [groups, setGroups] = useState<any[]>([]);
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [word, setWord] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [myWords, setMyWords] = useState<Record<number, string>>({});
    const [groupResult, setGroupResult] = useState<any>(null);

    const fetchGroups = async () => {
        const groupsResponse = await fetch(`${API_URL}/groups/me`, {
            credentials: "include"
        });
        if (groupsResponse.ok) {
            const data = await groupsResponse.json();
            setGroups(data);
        }
        const wordsResponse = await fetch(`${API_URL}/temperature/mine`, {
            credentials: "include"
        });
        if (wordsResponse.ok) {
            const data = await wordsResponse.json();
            const map: Record<number, string> = {};
            data.forEach((check: any) => { map[check.group_id] = check.word; }); // convert to a map so words can be looked up by group id
            setMyWords(map);
        }
    };

    const fetchGroupResult = async (groupId: number) => {
        const response = await fetch(`${API_URL}/temperature/group/${groupId}`, {
            credentials: "include"
        });
        if (response.ok) {
            const data = await response.json();
            setGroupResult(data);
        }
    };

    useEffect(() => {
        fetchGroups();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); // stops the page from reloading when it is submitted
        if (!selectedGroup) {
            alert("Please select a group.");
            return;
        }

        const trimmed = word.trim();
        if (!trimmed || trimmed.includes(" ")) {
            alert("Please enter a single word.");
            return;
        }

        setSubmitting(true);
        const response = await fetch(`${API_URL}/temperature/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ group_id: selectedGroup.id, word: trimmed })
        });
        setSubmitting(false);

        if (response.ok) {
            alert("Your word has been submitted.");
            setWord("");
            fetchGroups();
            fetchGroupResult(selectedGroup.id);
        } else {
            let message = "Something went wrong. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            alert(message);
        }
    };

    return (
        <main className = {styles.container}>
            <button className = {styles.back} onClick = {() => router.back()}>← Back</button>
            <h1 className = {styles.heading}>Weekly temperature check</h1>
            <p className = {styles.label}>Select a group</p>
            {groups.map(group => (
                <div
                    key = {group.id}
                    className = {(() => {
                        if (selectedGroup && selectedGroup.id === group.id) return `${styles.groupCard} ${styles.groupCardSelected}`;
                        return styles.groupCard;
                    })()}
                    onClick = {() => { setSelectedGroup(group); setGroupResult(null); fetchGroupResult(group.id); }}
                >
                    <p className = {styles.groupName}>{group.name}</p>
                    {myWords[group.id] !== undefined && (
                        <p className = {styles.wordText}>Your word this week: {myWords[group.id]}</p>
                    )}
                </div>
            ))}
            {selectedGroup && !myWords[selectedGroup.id] && (
                <div>
                    <p className = {styles.label}>In one word, how has the group been feeling this week?</p>
                    <input
                        className = {styles.input}
                        type = "text"
                        placeholder = "e.g. hopeful"
                        value = {word}
                        onChange = {(e) => setWord(e.target.value)}
                    />
                </div>
            )}
            {selectedGroup && !myWords[selectedGroup.id] && (
                <button
                    className = {styles.button}
                    onClick = {handleSubmit}
                    disabled = {submitting}
                >
                    {(() => {
                        if (submitting) return "Submitting...";
                        return "Submit";
                    })()}
                </button>
            )}
            {selectedGroup && groupResult && (
                <div className = {styles.resultsContainer}>
                    {(() => {
                        if (groupResult.revealed) {
                            return (
                                <div>
                                    <p className = {styles.resultsHeading}>This week's words</p>
                                    <p className = {styles.resultsText}>
                                        {Object.entries(groupResult.words as Record<string, number>)
                                            .sort((a, b) => b[1] - a[1])
                                            .map(([w, count]) => `${w} (${count})`)
                                            .join(" · ")}
                                    </p>
                                </div>
                            );
                        }
                        return <p className = {styles.waiting}>Waiting for more responses ({groupResult.response_count} so far)</p>;
                    })()}
                </div>
            )}
        </main>
    );
}