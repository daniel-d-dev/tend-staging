"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function TemperaturePage() {
    const [groups, setGroups] = useState<any[]>([]);
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [rating, setRating] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [myRatings, setMyRatings] = useState<Record<number, number>>({});

    const fetchGroups = async () => {
        const groupsResponse = await fetch(`${API_URL}/groups/me`, {
            credentials: "include"
        });
        if (groupsResponse.ok) {
            const data = await groupsResponse.json();
            setGroups(data);
        }
        const ratingsResponse = await fetch(`${API_URL}/temperature/mine`, {
            credentials: "include"
        });
        if (ratingsResponse.ok) {
            const data = await ratingsResponse.json();
            const map: Record<number, number> = {};
            data.forEach((check: any) => { map[check.group_id] = check.rating; }); // convert to a map so ratings can be looked up by group id
            setMyRatings(map);
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
            setSelectedGroup(null);
            setRating("");
            fetchGroups();
        } else if (response.status === 400) {
           alert("You have already rated this group this week.");
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
                    <p className = {styles.groupName}>{group.name}</p>
                    {myRatings[group.id] !== undefined && (
                        <p className = {styles.ratingText}>Your rating this week: {myRatings[group.id]}/5</p>
                    )}
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