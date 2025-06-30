import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";

const meta: Meta<typeof Button> = {
  component: Button,
  title: "ui/Button",
};

export default meta;

export const Primary: StoryObj<typeof Button> = {
  args: {
    children: "Click me",
  },
};
