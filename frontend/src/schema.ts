import { z } from "zod";

export const platformSchema = z.enum([
  "WhatsApp",
  "Instagram",
  "Telegram",
  "Facebook",
  "Email",
  "Other",
]);

export const platforms = platformSchema.options;
