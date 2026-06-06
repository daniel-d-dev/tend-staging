import { useEffect, useState } from "react";
import { Redirect } from "expo-router";
import { getToken } from "@/utils/token";

export default function Index() {
    const [isLoading, setIsLoading] = useState(true);
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        getToken().then((storedToken) => {
            setToken(storedToken);
            setIsLoading(false);
        });
    }, []);

    if (isLoading) return null;
    if (token) return <Redirect href="/(app)/dashboard" />;
    return <Redirect href="/(auth)/login" />;
}