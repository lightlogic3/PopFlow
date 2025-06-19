
module.exports = {
	root: true,
	env: {
		browser: true,
		node: true,
		es6: true,
	},

	parser: "vue-eslint-parser",

	parserOptions: {
		parser: "@typescript-eslint/parser",
		ecmaVersion: 2020,
		sourceType: "module",
		jsxPragma: "React",
		ecmaFeatures: {
			jsx: true,
		},
	},

	extends: [
		"prettier",
		"plugin:prettier/recommended",
		"plugin:vue/vue3-recommended",
		"plugin:@typescript-eslint/recommended",
	],

	plugins: ["eslint-plugin-prettier"],
	rules: {

		"no-var": "error",
		"no-multiple-empty-lines": ["error", { max: 1 }],
		"no-use-before-define": "off",
		"prefer-const": "off",
		"no-irregular-whitespace": "off",
		quotes: "off",


		"@typescript-eslint/no-unused-vars": "error",
		"@typescript-eslint/no-inferrable-types": "off",
		"@typescript-eslint/no-namespace": "off",
		"@typescript-eslint/no-explicit-any": "off",
		"@typescript-eslint/ban-ts-ignore": "off",
		"@typescript-eslint/ban-types": "off",
		"@typescript-eslint/explicit-function-return-type": "off",
		"@typescript-eslint/no-var-requires": "off",
		"@typescript-eslint/no-empty-function": "off",
		"@typescript-eslint/no-use-before-define": "off",
		"@typescript-eslint/ban-ts-comment": "off",
		"@typescript-eslint/no-non-null-assertion": "off",
		"@typescript-eslint/explicit-module-boundary-types": "off",
		"@typescript-eslint/quotes": ["error", "double"],


		"vue/no-v-html": "off",
		"vue/script-setup-uses-vars": "error",
		"vue/v-slot-style": "error",
		"vue/no-mutating-props": "off",
		"vue/custom-event-name-casing": "off",
		"vue/attributes-order": "off",
		"vue/one-component-per-file": "off",
		"vue/html-closing-bracket-newline": "off",
		"vue/max-attributes-per-line": "off",
		"vue/multiline-html-element-content-newline": "off",
		"vue/singleline-html-element-content-newline": "off",
		"vue/attribute-hyphenation": "off",
		"vue/require-default-prop": "off",
		"vue/multi-word-component-names": "off",
		"vue/html-self-closing": "off",
		"vue/html-indent": "off",
		"vue/html-quotes": ["error", "double"],


		"prettier/prettier": [
			"warn",
			{},
			{
				usePrettierrc: true,
			},
		],
	},
};
