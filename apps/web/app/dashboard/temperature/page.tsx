"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function TemperaturePage() {
    const [groups, setGroups] = useState<any[]>([]);
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [rating, setRating] = useState("");
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const fetchGroups = async () => {
            const response = await fetch(`${API_URL}/groups/me`, {
                credentials: "include"
            });
            if (response.ok) {
                const data = await response.json();
                setGroups(data);
            }
        };
        fetchGroups();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); // stops the page from reloading when it is submitted
        if (!selectedGroup) {
            alert("Please select a group.");
            return;
        }

        const ratingValue = parseInt(rating);
        if (ratingValue < 1 || ratingValue > 5) {
            alert("Rating must be between 1 and 5.");
            return;
        }

        setSubmitting(true);
        const response = await fetch(`${API_URL}/temperature/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ group_id: selectedGroup.id, rating: ratingValue })
        });
        setSubmitting(false);

        if (response.ok) {
            alert("Your rating has been submitted.");
        } else {
            alert("Something went wrong. Please try again.");
        }
    };

    return (
        <main className = {styles.container}>
            <h1 className = {styles.heading}>Weekly temperature check</h1>
            <p className = {styles.label}>Select a group</p>
            {groups.map(group => (
                <div
                    key = {group.id}
                    className = {(() => {
                        if (selectedGroup && selectedGroup.id === group.id) return `${styles.groupCard} ${styles.groupCardSelected}`;
                        return styles.groupCard;
                    })()}
                    onClick = {() => setSelectedGroup(group)}
                >
                    {group.name}
                </div>
            ))}
            {selectedGroup && (
                <div>
                    <p className = {styles.label}>How has the group been feeling this week? (1-5)</p>
                    <input
                        className = {styles.input}
                        type = "number"
                        min = "1"
                        max = "5"
                        placeholder = "1 = low, 5 = great"
                        value = {rating}
                        onChange = {(e) => setRating(e.target.value)}
                    />
                </div>
            )}
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
        </main>
    );
}