# React + TypeScript + Vite

このテンプレートは、ViteでReactを動作させるための最小限のセットアップを提供します（HMRといくつかのESLintルールを含みます）。

現在、2つの公式プラグインが利用可能です：

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) は [Babel](https://babeljs.io/) を使用してFast Refreshを実現します（[rolldown-vite](https://vite.dev/guide/rolldown)で使用される場合は [oxc](https://oxc.rs) を使用）。
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) は [SWC](https://swc.rs/) を使用してFast Refreshを実現します。

## React Compiler

このテンプレートでは、開発およびビルドのパフォーマンスへの影響を考慮し、React Compilerは有効になっていません。追加するには、[こちらのドキュメント](https://react.dev/learn/react-compiler/installation)を参照してください。

## ESLint設定の拡張

本番アプリケーションを開発している場合は、型認識（type-aware）のLintルールを有効にするために設定を更新することを推奨します：

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // その他の設定...

      // tseslint.configs.recommended を削除し、以下に置き換えます
      tseslint.configs.recommendedTypeChecked,
      // または、より厳格なルールを使用する場合
      tseslint.configs.strictTypeChecked,
      // オプションで、スタイルに関するルールを追加する場合
      tseslint.configs.stylisticTypeChecked,

      // その他の設定...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // その他のオプション...
    },
  },
])
```

また、React固有のLintルールとして [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) と [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) をインストールすることもできます：

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // その他の設定...
      // React用Lintルールを有効化
      reactX.configs['recommended-typescript'],
      // React DOM用Lintルールを有効化
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // その他のオプション...
    },
  },
])
```
