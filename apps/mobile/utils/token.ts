import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "auth_token"; // key used to store the JWT in secure storage

export async function saveToken(token: string): Promise<void> {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function getToken(): Promise<string | null> {
    return await SecureStore.getItemAsync(TOKEN_KEY)
}

export async function deleteToken(): Promise<void> {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
}