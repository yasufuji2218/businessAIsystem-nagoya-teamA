import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';

const { width } = Dimensions.get('window');

// ==========================================
// ダミーデータ（バックエンド連携予定）
// ==========================================
const DUMMY_DATA = {
  summary: {
    totalDetections24h: 47,
    topAnimals: [
      { species: 'イノシシ', count: 28, riskLevel: 'high', color: '#FF9800' },
      { species: 'クマ', count: 12, riskLevel: 'critical', color: '#FF0000' },
      { species: 'シカ', count: 7, riskLevel: 'low', color: '#4CAF50' },
    ],
  },
  timeSeriesData: [
    { hour: '0:00', detections: 2, label: '0' },
    { hour: '2:00', detections: 1, label: '2' },
    { hour: '4:00', detections: 3, label: '4' },
    { hour: '6:00', detections: 5, label: '6' },
    { hour: '8:00', detections: 8, label: '8' },
    { hour: '10:00', detections: 7, label: '10' },
    { hour: '12:00', detections: 6, label: '12' },
    { hour: '14:00', detections: 9, label: '14' },
    { hour: '16:00', detections: 6, label: '16' },
    { hour: '18:00', detections: 4, label: '18' },
    { hour: '20:00', detections: 3, label: '20' },
    { hour: '22:00', detections: 2, label: '22' },
  ],
  trapAreas: [
    { areaId: 1, areaName: '北尾根エリア', score: 8.7, detections: 24, frequency: 'very_high' },
    { areaId: 2, areaName: '南谷エリア', score: 7.2, detections: 18, frequency: 'high' },
    { areaId: 3, areaName: '東林道エリア', score: 6.5, detections: 13, frequency: 'medium' },
    { areaId: 4, areaName: '西台地エリア', score: 5.1, detections: 8, frequency: 'medium' },
    { areaId: 5, areaName: '中央湿地エリア', score: 3.8, detections: 4, frequency: 'low' },
  ],
};

// ==========================================
// サマリータイル
// ==========================================
const SummaryTile = ({ data }) => {
  return (
    <View style={styles.summaryContainer}>
      <Text style={styles.sectionTitle}>直近24時間の検知状況</Text>
      
      <View style={styles.totalDetectionsBox}>
        <Text style={styles.totalDetectionsLabel}>総検知数</Text>
        <Text style={styles.totalDetectionsValue}>{data.totalDetections24h}</Text>
        <Text style={styles.totalDetectionsUnit}>件</Text>
      </View>

      <Text style={styles.animalListTitle}>主要検知動物</Text>
      <View style={styles.animalListContainer}>
        {data.topAnimals.map((animal, index) => (
          <View key={index} style={styles.animalItemWrapper}>
            <View
              style={[
                styles.animalIndicator,
                { backgroundColor: animal.color },
              ]}
            />
            <View style={styles.animalTextContainer}>
              <Text style={styles.animalSpecies}>{animal.species}</Text>
              <Text style={styles.animalCount}>{animal.count}件</Text>
            </View>
            <View
              style={[
                styles.riskBadge,
                {
                  backgroundColor:
                    animal.riskLevel === 'critical'
                      ? '#FF0000'
                      : animal.riskLevel === 'high'
                      ? '#FF9800'
                      : '#4CAF50',
                },
              ]}
            >
              <Text style={styles.riskBadgeText}>
                {animal.riskLevel === 'critical'
                  ? '緊急'
                  : animal.riskLevel === 'high'
                  ? '要注意'
                  : '安全'}
              </Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
};

// ==========================================
// 出没傾向グラフ（モック棒グラフ）
// ==========================================
const TrendChart = ({ data }) => {
  const maxDetections = Math.max(...data.map(d => d.detections));

  return (
    <View style={styles.chartContainer}>
      <Text style={styles.sectionTitle}>時間帯別検知頻度</Text>
      <Text style={styles.chartSubtitle}>過去24時間のデータ</Text>
      
      <View style={styles.barChartWrapper}>
        <View style={styles.yAxisLabels}>
          <Text style={styles.yAxisLabel}>{maxDetections}</Text>
          <Text style={styles.yAxisLabel}>{Math.round(maxDetections / 2)}</Text>
          <Text style={styles.yAxisLabel}>0</Text>
        </View>

        <View style={styles.barsContainer}>
          {data.map((item, index) => {
            const barHeight = (item.detections / maxDetections) * 200;
            return (
              <View key={index} style={styles.barWrapper}>
                <View
                  style={[
                    styles.bar,
                    {
                      height: barHeight,
                      backgroundColor:
                        item.detections > 7
                          ? '#FF5722' // 赤系：高検知数
                          : item.detections > 4
                          ? '#FF9800' // オレンジ系：中検知数
                          : '#4CAF50', // 緑系：低検知数
                    },
                  ]}
                />
                <Text style={styles.barLabel}>{item.label}</Text>
              </View>
            );
          })}
        </View>
      </View>

      <View style={styles.chartLegend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#FF5722' }]} />
          <Text style={styles.legendLabel}>高（8件以上）</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#FF9800' }]} />
          <Text style={styles.legendLabel}>中（5-7件）</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: '#4CAF50' }]} />
          <Text style={styles.legendLabel}>低（4件以下）</Text>
        </View>
      </View>
    </View>
  );
};

// ==========================================
// 罠設置推奨エリアランキング
// ==========================================
const TrapAreaRanking = ({ data }) => {
  return (
    <View style={styles.rankingContainer}>
      <Text style={styles.sectionTitle}>罠設置推奨エリア</Text>
      <Text style={styles.rankingSubtitle}>スコア（出没頻度×慣れ度合い）の高い順</Text>

      <View style={styles.rankingListWrapper}>
        {data.map((area, index) => (
          <TouchableOpacity
            key={area.areaId}
            style={styles.rankingItem}
            activeOpacity={0.7}
          >
            <View style={styles.rankingRank}>
              <Text style={styles.rankingRankText}>{index + 1}</Text>
            </View>

            <View style={styles.rankingContent}>
              <Text style={styles.rankingAreaName}>{area.areaName}</Text>
              <View style={styles.frequencyRow}>
                <Text style={styles.frequencyLabel}>検知：</Text>
                <Text style={styles.frequencyValue}>{area.detections}件</Text>
              </View>
            </View>

            <View
              style={[
                styles.scoreBox,
                {
                  backgroundColor:
                    area.score >= 7
                      ? '#FF0000'
                      : area.score >= 5
                      ? '#FF9800'
                      : '#4CAF50',
                },
              ]}
            >
              <Text style={styles.scoreValue}>{area.score}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.actionButtonContainer}>
        <TouchableOpacity
          style={styles.actionButton}
          activeOpacity={0.8}
          onPress={() => console.log('詳細表示が押された')}
        >
          <Text style={styles.actionButtonText}>詳細を確認する</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.actionButtonSecondary]}
          activeOpacity={0.8}
          onPress={() => console.log('データ更新が押された')}
        >
          <Text style={[styles.actionButtonText, styles.actionButtonTextSecondary]}>
            データを更新
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ==========================================
// メインアプリケーション
// ==========================================
export default function WildlifeDashboard() {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setRefreshing(true);
    // シミュレーション：1秒後にリセット
    setTimeout(() => setRefreshing(false), 1000);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.container}
        showsVerticalScrollIndicator={true}
        scrollIndicatorInsets={{ right: 1 }}
      >
        {/* ヘッダー */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>データ分析ダッシュボード</Text>
          <Text style={styles.headerSubtitle}>野生動物検知データ</Text>
        </View>

        {/* リフレッシュボタン */}
        <TouchableOpacity
          style={styles.refreshButton}
          onPress={handleRefresh}
          activeOpacity={0.7}
        >
          <Text style={styles.refreshButtonText}>
            {refreshing ? '更新中...' : '🔄 データ更新'}
          </Text>
        </TouchableOpacity>

        {/* セクション1: サマリー */}
        <SummaryTile data={DUMMY_DATA.summary} />

        {/* セクション2: 出没傾向グラフ */}
        <TrendChart data={DUMMY_DATA.timeSeriesData} />

        {/* セクション3: 罠設置推奨エリア */}
        <TrapAreaRanking data={DUMMY_DATA.trapAreas} />

        {/* フッター余白 */}
        <View style={styles.footerSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ==========================================
// スタイル定義
// ==========================================
const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },

  // ヘッダー
  header: {
    paddingHorizontal: 20,
    paddingVertical: 24,
    backgroundColor: '#000000',
    borderBottomWidth: 3,
    borderBottomColor: '#FF5722',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#CCCCCC',
    marginTop: 4,
  },

  // リフレッシュボタン
  refreshButton: {
    marginHorizontal: 16,
    marginVertical: 16,
    paddingVertical: 16,
    paddingHorizontal: 24,
    backgroundColor: '#FF5722',
    borderRadius: 12,
    alignItems: 'center',
    minHeight: 60,
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  refreshButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },

  // セクションタイトル
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 16,
  },

  // ==================== サマリータイル ====================
  summaryContainer: {
    marginHorizontal: 16,
    marginVertical: 12,
    paddingHorizontal: 20,
    paddingVertical: 24,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    borderLeftWidth: 6,
    borderLeftColor: '#FF5722',
  },

  totalDetectionsBox: {
    alignItems: 'center',
    paddingVertical: 24,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#FF9800',
  },
  totalDetectionsLabel: {
    fontSize: 14,
    color: '#AAAAAA',
    marginBottom: 8,
    fontWeight: '600',
  },
  totalDetectionsValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#FF5722',
    lineHeight: 56,
  },
  totalDetectionsUnit: {
    fontSize: 18,
    color: '#FF9800',
    marginTop: 4,
    fontWeight: '600',
  },

  animalListTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  animalListContainer: {
    gap: 12,
  },
  animalItemWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#444444',
    minHeight: 60,
  },
  animalIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 14,
  },
  animalTextContainer: {
    flex: 1,
  },
  animalSpecies: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  animalCount: {
    fontSize: 13,
    color: '#999999',
  },
  riskBadge: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    minWidth: 60,
    alignItems: 'center',
    minHeight: 36,
    justifyContent: 'center',
  },
  riskBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  // ==================== グラフセクション ====================
  chartContainer: {
    marginHorizontal: 16,
    marginVertical: 12,
    paddingHorizontal: 20,
    paddingVertical: 24,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    borderLeftWidth: 6,
    borderLeftColor: '#4CAF50',
  },
  chartSubtitle: {
    fontSize: 13,
    color: '#999999',
    marginBottom: 20,
  },

  barChartWrapper: {
    flexDirection: 'row',
    height: 260,
    marginBottom: 24,
    alignItems: 'flex-end',
  },
  yAxisLabels: {
    width: 50,
    justifyContent: 'space-between',
    paddingRight: 8,
    paddingBottom: 0,
  },
  yAxisLabel: {
    fontSize: 11,
    color: '#888888',
    fontWeight: '500',
  },

  barsContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 3,
    paddingBottom: 20,
    borderLeftWidth: 2,
    borderBottomWidth: 2,
    borderColor: '#555555',
    paddingLeft: 8,
  },
  barWrapper: {
    flex: 1,
    alignItems: 'center',
    gap: 6,
  },
  bar: {
    width: '100%',
    borderRadius: 4,
    minHeight: 4,
  },
  barLabel: {
    fontSize: 10,
    color: '#888888',
    fontWeight: '500',
  },

  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#444444',
    gap: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    minHeight: 48,
    paddingHorizontal: 8,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 2,
  },
  legendLabel: {
    fontSize: 12,
    color: '#CCCCCC',
    fontWeight: '500',
  },

  // ==================== ランキングセクション ====================
  rankingContainer: {
    marginHorizontal: 16,
    marginVertical: 12,
    paddingHorizontal: 20,
    paddingVertical: 24,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    borderLeftWidth: 6,
    borderLeftColor: '#2196F3',
  },

  rankingSubtitle: {
    fontSize: 13,
    color: '#999999',
    marginBottom: 16,
  },

  rankingListWrapper: {
    gap: 12,
    marginBottom: 20,
  },
  rankingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#444444',
    minHeight: 80,
  },
  rankingRank: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  rankingRankText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  rankingContent: {
    flex: 1,
  },
  rankingAreaName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  frequencyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  frequencyLabel: {
    fontSize: 12,
    color: '#999999',
    fontWeight: '500',
  },
  frequencyValue: {
    fontSize: 14,
    color: '#FFD700',
    fontWeight: '600',
  },

  scoreBox: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
    minWidth: 60,
  },
  scoreValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  // ==================== アクションボタン ====================
  actionButtonContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: '#2196F3',
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 60,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  actionButtonSecondary: {
    backgroundColor: '#1a1a1a',
    borderWidth: 2,
    borderColor: '#2196F3',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  actionButtonTextSecondary: {
    color: '#2196F3',
  },

  // フッター余白
  footerSpacer: {
    height: 32,
  },
});
