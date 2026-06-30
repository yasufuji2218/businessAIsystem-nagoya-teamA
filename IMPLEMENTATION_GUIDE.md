# 獣害対策ダッシュボード - 実装ガイド

## 📋 概要
屋外での使用を想定した、視認性と操作性を最優先にした野生動物検知ダッシュボード。

## 🚀 セットアップ手順

### 1. Expo プロジェクトの初期化
```bash
# 新規プロジェクトを作成（すでにある場合はスキップ）
npx create-expo-app WildlifeDashboard
cd WildlifeDashboard
```

### 2. コードの配置
上記の `WildlifeDashboard.js` を以下の いずれかで使用：

**方法 A: `App.js` として置き換え**
```bash
# App.jsをバックアップ
cp App.js App.js.bak

# 新しいコードで置き換え
cp WildlifeDashboard.js App.js
```

**方法 B: 別ファイルとして追加 + App.jsで import**
```javascript
// App.js
import WildlifeDashboard from './WildlifeDashboard';
export default WildlifeDashboard;
```

### 3. アプリを起動
```bash
# iOS（Mac必須）
npx expo run:ios

# Android
npx expo run:android

# Web での確認
npx expo run:web
```

---

## 🎨 デザイン原則の実装

### ✅ 実装済みの特徴

#### 1. **視認性優先**
- **高コントラスト**: 黒背景 (#1a1a1a) × 白テキスト で、直射日光下でも読みやすい
- **フォントサイズ**: 本文最小13px、タイトル22px以上
- **色の使い分け**:
  - 🔴 クマ/緊急: #FF0000（赤）
  - 🟠 イノシシ/要注意: #FF9800（オレンジ）
  - 🟢 シカ/安全: #4CAF50（緑）

#### 2. **操作性優先**
- **タップ領域**: すべてのボタン・リスト項目が最小60x60px
- **マージン**: 要素間に十分な余白（16px以上）
- **フォーカス**: `activeOpacity` で軍手対応のフィードバック
- **余白設計**: パディング 20-24px で誤タップ防止

#### 3. **屋外での実務性**
- **スクロール対応**: 3セクション縦スクロール、長時間読める設計
- **情報優先順位**: 最重要（総検知数）→ 次点（時間帯別）→ 詳細（エリア別）
- **リアルタイム更新**: 「データ更新」ボタンで最新情報を取得可能

---

## 🔧 カスタマイズ方法

### 1. ダミーデータの変更

```javascript
// DUMMY_DATA オブジェクトを編集

const DUMMY_DATA = {
  summary: {
    totalDetections24h: 47,  // ← 数字を変更
    topAnimals: [
      // 動物を追加/削除
      { species: '新しい動物', count: 10, riskLevel: 'high', color: '#FF9800' },
    ],
  },
  // ... その他のセクション
};
```

### 2. 色のカスタマイズ

#### パレット変更例（夜間用オレンジテーマ）
```javascript
// header の borderBottomColor
borderBottomColor: '#FFB74D',  // オレンジに変更

// リフレッシュボタン
backgroundColor: '#FF9800',  // オレンジ

// 各バー色
backgroundColor: item.detections > 7
  ? '#FFB74D'  // 明るいオレンジ
  : '#FF9800'  // 標準オレンジ
  : '#66BB6A',  // 緑
```

### 3. フォントサイズの調整（高齢者対応など）

```javascript
// styles オブジェクト内で一括変更
headerTitle: {
  fontSize: 32,  // 28 → 32 に拡大
},
animalSpecies: {
  fontSize: 18,  // 16 → 18 に拡大
},
// ... その他を同様に
```

### 4. セクションの追加

例：「アラート・通知」セクションを追加する場合

```javascript
// SummaryTile の後に新しいコンポーネント作成
const AlertSection = ({ alerts }) => {
  return (
    <View style={styles.alertContainer}>
      <Text style={styles.sectionTitle}>⚠️ 緊急アラート</Text>
      {alerts.map((alert, idx) => (
        <View key={idx} style={styles.alertItem}>
          <Text style={styles.alertText}>{alert.message}</Text>
        </View>
      ))}
    </View>
  );
};

// App.js 内で使用
<AlertSection alerts={[
  { message: '北尾根エリアでクマが検知されました' },
]} />
```

---

## 📱 バックエンド連携（今後の拡張）

### データ取得の実装例

```javascript
import { useState, useEffect } from 'react';

export default function WildlifeDashboard() {
  const [data, setData] = useState(DUMMY_DATA);
  const [loading, setLoading] = useState(false);

  // マウント時に API からデータ取得
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        'https://your-api.com/api/v1/wildlife-data'
      );
      const json = await response.json();
      setData(json);
    } catch (error) {
      console.error('データ取得エラー:', error);
      // エラー時はダミーデータを使用
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchData();
  };

  // ... 残りのコンポーネント
}
```

---

## 🔐 セキュリティ・プライバシー対応

### 推奨事項

1. **センシティブ情報の管理**
   - API キーは `.env` ファイルで環境変数として管理
   - 位置情報は必要最小限で取得

2. **オフライン対応**
   ```javascript
   import AsyncStorage from '@react-native-async-storage/async-storage';
   
   const saveDashboardData = async (data) => {
     try {
       await AsyncStorage.setItem('dashboardData', JSON.stringify(data));
     } catch (error) {
       console.error('保存エラー:', error);
     }
   };
   ```

3. **ネットワークセキュリティ**
   - HTTPS のみを使用
   - API 呼び出しにタイムアウトを設定

---

## 🧪 テスト方法

### ビジュアルテスト
- **Expo Go アプリ**で実機テスト（Android/iOS）
- **Expo Web** でブラウザ確認
- 異なる画面サイズでのレスポンシブ確認

### ユーザビリティテスト
- 軍手装着下での操作テスト
- 屋外（直射日光）での視認性テスト
- タップ領域（60x60px 最小）の確認

### コード品質
```bash
# ESLint でチェック（推奨）
npm install --save-dev eslint eslint-plugin-react-native
npx eslint WildlifeDashboard.js
```

---

## 📊 パフォーマンス最適化

### 推奨事項

1. **リスト最適化** - 大量のアイテムは `FlatList` に変更
   ```javascript
   import { FlatList } from 'react-native';
   
   <FlatList
     data={DUMMY_DATA.trapAreas}
     renderItem={({ item, index }) => (
       <RankingItem item={item} index={index} />
     )}
     keyExtractor={(item) => item.areaId.toString()}
   />
   ```

2. **メモ化** - 不要な再レンダリングを防止
   ```javascript
   const SummaryTile = React.memo(({ data }) => {
     // ... 実装
   });
   ```

3. **画像の最適化** - 将来的にアイコン追加時
   ```javascript
   import { Image } from 'react-native';
   
   <Image
     source={require('./assets/bear-icon.png')}
     style={{ width: 24, height: 24 }}
   />
   ```

---

## 🌐 多言語対応（将来の拡張）

```javascript
const translations = {
  ja: {
    totalDetections: '総検知数',
    dataUpdate: 'データ更新',
  },
  en: {
    totalDetections: 'Total Detections',
    dataUpdate: 'Update Data',
  },
};

// 使用例
const lang = 'ja';
<Text>{translations[lang].totalDetections}</Text>
```

---

## 📝 トラブルシューティング

### Q: アプリが起動しない
```bash
# キャッシュをクリア
npx expo start --clear
```

### Q: データが表示されない
1. `DUMMY_DATA` のフォーマットを確認
2. コンソール（`expo start` の出力）でエラーを確認
3. Android は `adb logcat`、iOS は Xcode コンソール

### Q: タップが反応しない
- `minHeight: 60` が設定されているか確認
- `TouchableOpacity` の `activeOpacity` プロップを確認

### Q: 屋外で見えない
- 背景色が十分に濃いか確認（推奨: #1a1a1a 以下）
- テキストが十分に明るいか確認（推奨: #FFFFFF または #CCCCCC）

---

## 📚 参考リソース

- **React Native ドキュメント**: https://reactnative.dev
- **Expo ドキュメント**: https://docs.expo.dev
- **StyleSheet API**: https://reactnative.dev/docs/stylesheet
- **アクセシビリティ**: https://reactnative.dev/docs/accessibility

---

## 🚀 次のステップ

1. **バックエンド API 構築** - Node.js / Python での実装
2. **ローカルデータベース** - SQLite for React Native
3. **位置情報サービス** - Geolocation API との統合
4. **プッシュ通知** - FCM / APNs での緊急アラート
5. **オフラインマップ** - React Native Maps

---

## 📞 サポート

実装時にご質問がある場合は、以下をご確認ください：
1. エラーメッセージの詳細
2. 使用している Expo / React Native のバージョン
3. 再現手順

---

**Last Updated**: 2026-06-23  
**Version**: 1.0.0
