import { cookieStorage, createStorage } from "@wagmi/core";
import { WagmiAdapter } from "@reown/appkit-adapter-wagmi";
import { baseSepolia, base } from "@reown/appkit/networks";

// Get projectId from https://cloud.reown.com
export const projectId = "9ddc562e573db800e21f1f70fcc23773";

if (!projectId) {
    throw new Error("Project ID is not defined");
}

export const networks = [baseSepolia, base];

//Set up the Wagmi Adapter (Config)
export const wagmiAdapter = new WagmiAdapter({
    storage: createStorage({
        storage: cookieStorage,
    }),
    ssr: true,
    projectId,
    networks,
});

export const config = wagmiAdapter.wagmiConfig;
