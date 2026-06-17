"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function GroupsPage() {
    const [groups, setGroups] = useState<any[]>([]);
    const [groupName, setGroupName] = useState("");
    const [joinCode, setJoinCode] = useState("");
    const [creating, setCreating] = useState(false);
    const [joining, setJoining] = useState(false);

    const fetchGroups = async () => {
        const response = await fetch(`${API_URL}/groups/me`, {
            credentials: "include"
        });
        if (response.ok) {
            const data = await response.json();
            setGroups(data);
        }
    };

    useEffect(() => {
        fetchGroups();
    }, []);

    const handleCreateGroup = async () => {
        if (!groupName.trim()) {
            alert("Please enter a group name.");
            return;
        }
        setCreating(true);
        const response = await fetch(`${API_URL}/groups/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ name: groupName.trim() })
        });
        setCreating(false);
        if (response.ok) {
            setGroupName("");
            const data = await response.json();
            setGroups(prev => [...prev, data]);
        } else {
            alert("Could not create group. Please try again.");
        }
    };

    const handleJoinGroup = async () => {
        if (!joinCode.trim()) {
            alert("Please enter a join code.");
            return;
        }
        setJoining(true);
        const response = await fetch(`${API_URL}/groups/join?join_code=${joinCode.trim().toUpperCase()}`, {
            method: "POST",
            credentials: "include"
        });
        setJoining(false);
        if (response.ok) {
            setJoinCode("");
            fetchGroups();
        } else {
            alert("Could not join group. Please try again.");
        }
    };

    return (
        <main className = {styles.container}>
            <h1 className = {styles.heading}>My Groups</h1>

            {groups.length === 0 && (
                <p className = {styles.empty}>You are not in any groups yet.</p>
            )}

            {groups.map(group => (
                <div key = {group.id} className = {styles.groupCard}>
                    <p className = {styles.groupName}>{group.name}</p>
                    <p className = {styles.joinCode}>Join code: {group.join_code}</p>
                </div>
            ))}

            <h2 className = {styles.sectionHeading}>Create a group</h2>
            <input
                className = {styles.input}
                placeholder = "Group name"
                value = {groupName}
                onChange = {(e) => setGroupName(e.target.value)}
            />
            <button
                className = {styles.button}
                onClick = {handleCreateGroup}
                disabled = {creating}
            >
                {(() => {
                    if (creating) return "Creating...";
                    return "Create group";
                })()}
            </button>

            <h2 className = {styles.sectionHeading}>Join a group</h2>
            <input
                className = {styles.input}
                placeholder = "Enter join code"
                value = {joinCode}
                onChange = {(e) => setJoinCode(e.target.value)}
            />
            <button
                className = {styles.button}
                onClick = {handleJoinGroup}
                disabled = {joining}
            >
                {(() => {
                    if (joining) return "Joining...";
                    return "Join group";
                })()}
            </button>
        </main>
    );
}