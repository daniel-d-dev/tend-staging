import { useState, useCallback } from "react";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getToken } from "@/utils/token";
import { API_URL } from "@/constants/api";

type ReactionData = {
    id: number;
    post_id: number;
    user_id: number;
    emoji: string;
};

type PostData = {
    id: number;
    group_id: number;
    author_id: number | null;
    author_name: string | null;
    content: string;
    author_type: string;
    parent_post_id: number | null;
    parent_author: string | null;
    parent_content: string | null;
    created_at: string;
    reactions: ReactionData[];
};

const EMOJIS = ["❤️", "👍", "😔", "💪", "🙏"];

export default function FeedScreen() {
    const { group_id, name } = useLocalSearchParams<{ group_id: string; name: string }>();
    const router = useRouter();
    const [posts, setPosts] = useState<PostData[]>([]);
    const [newPost, setNewPost] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [replyingTo, setReplyingTo] = useState<number | null>(null);
    const [currentUserId, setCurrentUserId] = useState<number | null>(null);
    const [openPickerPostId, setOpenPickerPostId] = useState<number | null>(null);

    const fetchFeed = async () => {
        const token = await getToken();
        const [feedResponse, meResponse] = await Promise.all([ // we need the user's id to know which reactions are theirs
            fetch(`${API_URL}/feed/groups/${group_id}`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            fetch(`${API_URL}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` }
            })
        ]);
        if (feedResponse.ok) {
            const data = await feedResponse.json();
            setPosts(data)
        }
        if (meResponse.ok) {
            const me = await meResponse.json();
            setCurrentUserId(me.id)
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchFeed();
        }, [])
    );

    const handlePost = async () => {
        if (!newPost.trim()) {
            return;
        }
        setSubmitting(true);
        const token = await getToken();
        let url = `${API_URL}/feed/groups/${group_id}`;
        if (replyingTo) {
            url = `${API_URL}/feed/posts/${replyingTo}/reply`
        }
        const response = await fetch(url, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ content: newPost.trim() })
        });
        setSubmitting(false)
        if (response.ok) {
            setNewPost("");
            setReplyingTo(null);
            fetchFeed();
        }
    };

    const handleReact = async (postId: number, emoji: string, alreadyReacted: boolean) => {
        const token = await getToken();
        if (alreadyReacted) {
            await fetch(`${API_URL}/feed/posts/${postId}/react?emoji=${emoji}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });
        } else {
            await fetch(`${API_URL}/feed/posts/${postId}/react`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ emoji })
            });
        }
        fetchFeed();
    };

    const renderPost = ({ item }: { item: PostData }) => {
        const isAgent = item.author_type === "agent";
        let authorDisplay = item.author_name;
        if (isAgent) {
            authorDisplay = "Thread"; // agent posts surface as system messages and are not attributed to a person
        }

        return (
            <View style = {[styles.post, isAgent && styles.agentPost]}>
                <Text style = {[styles.author, isAgent && styles.agentAuthor]}>
                    {authorDisplay}
                </Text>
                {item.parent_content && (
                    <View style = {styles.replyContext}>
                        <Text style = {styles.replyContextText} numberOfLines = {2}>↳ {item.parent_author}: {item.parent_content}</Text>
                    </View>
                )}
                <Text style = {styles.content}>{item.content}</Text>
                <Text style = {styles.timestamp}>
                    {new Date(item.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                </Text>

                <View style = {styles.reactions}>
                    {item.reactions
                        .filter((r, index, self) => self.findIndex(x => x.emoji === r.emoji) === index) // if multiple people reacted with the same emoji, only keep the first occurrence but show the count separately
                        .map(r => {
                            const count = item.reactions.filter(x => x.emoji === r.emoji).length;
                            const reacted = item.reactions.some(x => x.emoji === r.emoji && x.user_id === currentUserId);
                            return (
                                <TouchableOpacity
                                    key = {r.emoji}
                                    style = {[styles.emojiButton, reacted && styles.emojiActive]}
                                    onPress = {() => handleReact(item.id, r.emoji, reacted)}
                                >
                                    <Text style = {styles.emojiText}>{r.emoji} {count}</Text>
                                </TouchableOpacity>
                            );
                        })
                    }
                    {openPickerPostId === item.id && (
                        <View style = {styles.emojiPicker}>
                            {EMOJIS.map(emoji => (
                                <TouchableOpacity
                                    key = {emoji}
                                    onPress = {() => {
                                        const reacted = item.reactions.some(r => r.emoji === emoji && r.user_id === currentUserId);
                                        handleReact(item.id, emoji, reacted);
                                        setOpenPickerPostId(null);
                                    }}
                                >
                                    <Text style = {styles.emojiPickerOption}>{emoji}</Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                    )}
                    
                    <TouchableOpacity onPress = {() => setOpenPickerPostId(openPickerPostId === item.id ? null : item.id)}>
                        <Text style = {styles.addReaction}>+</Text>
                    </TouchableOpacity>
                </View>

                {!item.parent_post_id && ( // only top level posts get a reply button. Can't reply to a reply
                    <TouchableOpacity onPress = {() => setReplyingTo(item.id)}>
                        <Text style = {styles.replyButton}>Reply</Text>
                    </TouchableOpacity>
                )}
            </View>
        );
    };

    return (
        <SafeAreaView style = {styles.container}>
            <KeyboardAvoidingView style = {styles.inner} behavior = {Platform.OS === "ios" ? "padding" : undefined}>
                <View style = {styles.header}>
                    <TouchableOpacity onPress = {() => router.back()}>
                        <Text style = {styles.back}>Back</Text>
                    </TouchableOpacity>
                    <Text style = {styles.heading}>{name}</Text>
                </View>
                <FlatList
                    data = {posts}
                    keyExtractor = {item => item.id.toString()}
                    renderItem = {renderPost}
                    contentContainerStyle = {styles.list}
                />
                {replyingTo && (
                    <Text style = {styles.replyingLabel}>
                        Replying to a post: <Text onPress = {() => setReplyingTo(null)}>cancel</Text>
                    </Text>
                )}
                <View style = {styles.inputRow}>
                    <TextInput
                        style = {styles.input}
                        placeholder = {replyingTo ? "Write a reply..." : "Write something..."}
                        value = {newPost}
                        onChangeText = {setNewPost}
                        multiline
                    />
                    <TouchableOpacity
                        style = {styles.sendButton}
                        onPress = {handlePost}
                        disabled = {submitting}
                    >
                        <Text style = {styles.sendText}>Post</Text>
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    inner: {
        flex: 1,
    },
    header: {
        flexDirection: "row",
        alignItems: "center",
        gap: 16,
        padding: 24,
        paddingBottom: 12,
    },
    back: {
        fontSize: 15,
    },
    heading: {
        fontSize: 18,
        fontWeight: "600",
    },
    list: {
        padding: 16,
        paddingBottom: 24,
    },
    post: {
        backgroundColor: "#f9f9f9",
        borderRadius: 10,
        padding: 14,
        marginBottom: 12,
    },
    agentPost: {
        backgroundColor: "#EEF4FF",
        borderLeftWidth: 3,
        borderLeftColor: "#3A5880",
    },
    author: {
        fontSize: 13,
        fontWeight: "600",
        marginBottom: 4,
    },
    agentAuthor: {
        color: "#3A5880",
    },
    content: {
        fontSize: 15,
        lineHeight: 22,
        marginBottom: 8,
    },
    timestamp: {
        fontSize: 11,
        color: "#999",
        marginBottom: 8,
    },
    reactions: {
        flexDirection: "row",
        gap: 8,
        flexWrap: "wrap",
        marginBottom: 8,
    },
    emojiButton: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
        backgroundColor: "#eee",
    },
    emojiActive: {
        backgroundColor: "#d0e4ff",
    },
    emojiText: {
        fontSize: 14,
    },
    replyButton: {
        fontSize: 12,
        color: "#555",
    },
    replyingLabel: {
        padding: 8,
        paddingHorizontal: 16,
        fontSize: 13,
        color: "#555",
        backgroundColor: "#f0f0f0",
    },
    inputRow: {
        flexDirection: "row",
        alignItems: "flex-end",
        gap: 8,
        padding: 12,
        borderTopWidth: 1,
        borderTopColor: "#eee",
    },
    input: {
        flex: 1,
        borderWidth: 1,
        borderColor: "#ccc",
        borderRadius: 8,
        padding: 10,
        fontSize: 15,
        maxHeight: 100,
    },
    sendButton: {
        backgroundColor: "#000",
        paddingVertical: 10,
        paddingHorizontal: 16,
        borderRadius: 8,
    },
    sendText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 14,
    },
    emojiPicker: {
        flexDirection: "row",
        gap: 8,
        marginBottom: 4,
    },
    emojiPickerOption: {
        fontSize: 20,
    },
    addReaction: {
        fontSize: 18,
        color: "#999",
        paddingHorizontal: 6,
    },
    replyContext: {
        borderLeftWidth: 2,
        borderLeftColor: "#ccc",
        paddingLeft: 8,
        marginBottom: 8,
    },
    replyContextText: {
        fontSize: 12,
        color: "#888"
    }
});