import { useUserStore } from "@/store/user";

/**
 * 检查用户是否具有特定权限
 * @param permission 需要检查的权限
 * @returns 是否具有权限
 */
export function hasPermission(permission: string): boolean {
	const userStore = useUserStore();

	// 1. 如果用户有admin角色，直接返回true，拥有所有权限
	if (userStore.roles.includes("admin")) {
		return true;
	}

	// 2. 否则检查用户是否拥有特定权限
	return userStore.permissions.includes(permission);
}

/**
 * 检查用户是否具有特定角色
 * @param role 需要检查的角色
 * @returns 是否具有角色
 */
export function hasRole(role: string): boolean {
	const userStore = useUserStore();
	return userStore.roles.includes(role);
}

/**
 * 检查用户是否具有指定角色列表中的任意一个角色
 * @param roles 角色列表
 * @returns 是否具有指定角色中的任意一个
 */
export function hasAnyRole(roles: string[]): boolean {
	const userStore = useUserStore();
	return roles.some((role) => userStore.roles.includes(role));
}

/**
 * 检查用户是否具有指定权限列表中的所有权限
 * @param permissions 权限列表
 * @returns 是否具有所有指定权限
 */
export function hasAllPermissions(permissions: string[]): boolean {
	const userStore = useUserStore();

	// 如果用户有admin角色，直接返回true
	if (userStore.roles.includes("admin")) {
		return true;
	}

	return permissions.every((permission) => userStore.permissions.includes(permission));
}

/**
 * 检查用户是否具有指定权限列表中的任意一个权限
 * @param permissions 权限列表
 * @returns 是否具有任意一个指定权限
 */
export function hasAnyPermission(permissions: string[]): boolean {
	const userStore = useUserStore();

	// 如果用户有admin角色，直接返回true
	if (userStore.roles.includes("admin")) {
		return true;
	}

	return permissions.some((permission) => userStore.permissions.includes(permission));
}
