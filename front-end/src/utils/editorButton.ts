import user from "@/assets/prompt/user.png";
import role from "@/assets/prompt/role.png";
import line from "@/assets/prompt/line.png";
import relationship from "@/assets/prompt/relationship.png";
import context from "@/assets/prompt/context.png";
import hideDeeigns from "@/assets/prompt/hideDeeigns.png";
import personality from "@/assets/prompt/personality.png";
import taskGoal from "@/assets/prompt/taskGoal.png";

export const globalPrompt = [
	{ value: "user", name: "User", avatar: user },
	{ value: "role", name: "NPC Info", avatar: role },
	{ value: "dialogue", name: "Dialog Examples", avatar: line },
	{ value: "relationship", name: "User Relationship", avatar: relationship },
	{ value: "context", name: "Knowledge Prompt", avatar: context },
];

export const taskPrompt = [
	{ value: "user", name: "User", avatar: user },
	{ value: "taskDescription", name: "Task Description", avatar: line },
	{ value: "taskGoal", name: "Task Goal", avatar: taskGoal },
	{ value: "taskPersonality", name: "Task Character", avatar: personality },
	{ value: "context", name: "Knowledge Prompt", avatar: context },
	{ value: "role", name: "NPC Info", avatar: role },
	{ value: "hideDesigns", name: "Hidden Settings", avatar: hideDeeigns },
];

export const rolePrompt = [{ value: "user", name: "User", avatar: user }];
