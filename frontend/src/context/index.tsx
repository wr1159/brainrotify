// context/index.tsx
"use client";

import { wagmiAdapter, projectId } from "@/config";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createAppKit } from "@reown/appkit/react";
import { base, baseSepolia } from "@reown/appkit/networks";
import React, { type ReactNode } from "react";
import { cookieToInitialState, WagmiProvider, type Config } from "wagmi";

// Set up queryClient
const queryClient = new QueryClient();

if (!projectId) {
    throw new Error("Project ID is not defined");
}

// Set up metadata
const metadata = {
    name: "brainrotify",
    description: "AppKit Example",
    url: "https://brainrotify-topaz.vercel.app/", // origin must match your domain & subdomain
    icons: ["https://assets.reown.com/reown-profile-pic.png"],
};

// Create the modal
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const modal = createAppKit({
    adapters: [wagmiAdapter],
    projectId,
    networks: [base, baseSepolia],
    metadata: metadata,
    features: {
        analytics: true, // Optional - defaults to your Cloud configuration
    },
});

function ContextProvider({
    children,
    cookies,
}: {
    children: ReactNode;
    cookies: string | null;
}) {
    const initialState = cookieToInitialState(
        wagmiAdapter.wagmiConfig as Config,
        cookies
    );

    return (
        <WagmiProvider
            config={wagmiAdapter.wagmiConfig as Config}
            initialState={initialState}
        >
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        </WagmiProvider>
    );
}

export default ContextProvider;
