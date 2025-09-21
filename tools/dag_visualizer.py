#!/usr/bin/env python3
"""
DAG 시각화 도구 - Graphviz & Mermaid
외부 레퍼런스: 
- https://graphviz.readthedocs.io/
- https://mermaid.js.org/intro/

사용법:
    python tools/dag_visualizer.py --input tasks.reflected.json --format graphviz
    python tools/dag_visualizer.py --input tasks.reflected.json --format mermaid
    python tools/dag_visualizer.py --input tasks.reflected.json --format both
"""

import json
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Graphviz imports
try:
    from graphviz import Digraph
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    # Digraph 클래스를 더미로 정의하여 타입 힌트 오류 방지
    class Digraph:
        pass

# Mermaid은 텍스트 기반이므로 별도 라이브러리 불필요

@dataclass
class TaskNode:
    """태스크 노드 정보"""
    id: str
    title: str
    type: str
    module: str
    complexity: float
    deps: List[str]
    order: Optional[int] = None
    status: str = "pending"  # pending, in_progress, completed

class DAGVisualizer:
    """DAG 시각화 도구"""
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.tasks: Dict[str, TaskNode] = {}
        self.task_list: List[TaskNode] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_deps: Dict[str, Set[str]] = {}
        
        # 시각화 설정
        self.colors = {
            'code': '#FF6B6B',      # 빨강
            'config': '#4ECDC4',    # 청록
            'cli': '#45B7D1',       # 파랑
            'mcp': '#96CEB4',       # 연두
            'ide': '#FFEAA7',       # 노랑
            'test': '#DDA0DD',      # 자주
            'doc': '#98D8C8',       # 민트
            'default': '#95A5A6'    # 회색
        }
        
        self.complexity_colors = {
            'low': '#2ECC71',       # 초록 (0.0-1.0)
            'medium': '#F39C12',    # 주황 (1.0-2.0)
            'high': '#E74C3C',      # 빨강 (2.0+)
            'critical': '#8E44AD'   # 보라 (3.0+)
        }
    
    def load_tasks(self):
        """태스크 데이터 로드"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 태스크 파싱
            for task_data in data.get('tasks', []):
                task = TaskNode(
                    id=task_data['id'],
                    title=task_data['title'],
                    type=task_data.get('type', 'default'),
                    module=task_data.get('module', 'unknown'),
                    complexity=task_data.get('complexity', 1.0),
                    deps=task_data.get('deps', []),
                    order=task_data.get('order')
                )
                
                self.tasks[task.id] = task
                self.task_list.append(task)
            
            # 의존성 그래프 구성
            self._build_dependency_graph()
            
            print(f"✅ {len(self.tasks)}개 태스크 로드 완료")
            
        except Exception as e:
            print(f"❌ 태스크 로드 실패: {e}")
            sys.exit(1)
    
    def _build_dependency_graph(self):
        """의존성 그래프 구성"""
        for task in self.task_list:
            self.dependency_graph[task.id] = set(task.deps)
            
            # 역방향 의존성 구성
            if task.id not in self.reverse_deps:
                self.reverse_deps[task.id] = set()
            
            for dep in task.deps:
                if dep not in self.reverse_deps:
                    self.reverse_deps[dep] = set()
                self.reverse_deps[dep].add(task.id)
    
    def _get_complexity_color(self, complexity: float) -> str:
        """복잡도에 따른 색상 반환"""
        if complexity >= 3.0:
            return self.complexity_colors['critical']
        elif complexity >= 2.0:
            return self.complexity_colors['high']
        elif complexity >= 1.0:
            return self.complexity_colors['medium']
        else:
            return self.complexity_colors['low']
    
    def _get_task_color(self, task_type: str) -> str:
        """태스크 타입에 따른 색상 반환"""
        return self.colors.get(task_type, self.colors['default'])
    
    def generate_graphviz_dag(self, output_file: str = "tasks_dag"):
        """Graphviz DAG 생성"""
        if not GRAPHVIZ_AVAILABLE:
            print("❌ Graphviz가 설치되지 않음. pip install graphviz 실행 필요")
            return False
        
        print("🎨 Graphviz DAG 생성 중...")
        
        try:
            # Digraph 생성
            dot = Digraph(comment='Task DAG')
            dot.attr(rankdir='TB', size='12,8')  # Top-Bottom 레이아웃
            dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
            dot.attr('edge', fontname='Arial', fontsize='8')
            
            # 노드 생성
            for task in self.task_list:
                # 노드 라벨 구성
                label = f"{task.id}\\n{task.title[:30]}{'...' if len(task.title) > 30 else ''}\\nC={task.complexity:.2f}"
                
                # 색상 결정 (복잡도 우선)
                if task.complexity >= 2.0:
                    fillcolor = self._get_complexity_color(task.complexity)
                else:
                    fillcolor = self._get_task_color(task.type)
                
                # 노드 추가
                dot.node(
                    task.id,
                    label=label,
                    fillcolor=fillcolor,
                    fontcolor='white' if task.complexity >= 2.0 else 'black'
                )
            
            # 엣지 생성 (의존성)
            for task in self.task_list:
                for dep in task.deps:
                    if dep in self.tasks:
                        # 임계 경로 강조 (높은 복잡도 태스크들)
                        if task.complexity >= 2.0 or self.tasks[dep].complexity >= 2.0:
                            dot.edge(dep, task.id, color='red', penwidth='2')
                        else:
                            dot.edge(dep, task.id, color='gray')
            
            # 레이아웃 최적화
            self._optimize_graphviz_layout(dot)
            
            # 파일 출력
            dot.render(output_file, format='svg', cleanup=True)
            dot.render(output_file, format='png', cleanup=True)
            
            print(f"✅ Graphviz DAG 생성 완료:")
            print(f"  • SVG: {output_file}.svg")
            print(f"  • PNG: {output_file}.png")
            
            return True
            
        except Exception as e:
            print(f"❌ Graphviz DAG 생성 실패: {e}")
            return False
    
    def _optimize_graphviz_layout(self, dot: Digraph):
        """Graphviz 레이아웃 최적화"""
        # 임계 경로 식별 및 강조
        critical_path = self._find_critical_path()
        
        # 임계 경로 태스크들을 같은 레벨에 배치
        if critical_path:
            with dot.subgraph(name='cluster_critical') as c:
                c.attr(style='filled', color='lightgray', label='Critical Path')
                for task_id in critical_path:
                    if task_id in self.tasks:
                        c.node(task_id)
        
        # 모듈별 그룹화
        modules = {}
        for task in self.task_list:
            module = task.module
            if module not in modules:
                modules[module] = []
            modules[module].append(task.id)
        
        for module, task_ids in modules.items():
            if len(task_ids) > 1:
                with dot.subgraph(name=f'cluster_{module}') as c:
                    c.attr(style='filled', color='lightblue', label=f'Module: {module}')
                    for task_id in task_ids:
                        c.node(task_id)
    
    def _find_critical_path(self) -> List[str]:
        """임계 경로 찾기 (최장 경로)"""
        # 간단한 임계 경로 알고리즘 (복잡도 기반)
        critical_tasks = []
        
        for task in self.task_list:
            if task.complexity >= 2.0:
                critical_tasks.append(task.id)
        
        return critical_tasks
    
    def generate_mermaid_gantt(self, output_file: str = "tasks_gantt.md"):
        """Mermaid Gantt 차트 생성"""
        print("📊 Mermaid Gantt 차트 생성 중...")
        
        try:
            # 시작 날짜 설정 (오늘부터)
            start_date = datetime.now()
            
            # Mermaid Gantt 템플릿
            gantt_content = f"""# 태스크 실행 계획 (Gantt Chart)

```mermaid
gantt
    title Hybrid AI Development Workflow
    dateFormat  YYYY-MM-DD
    axisFormat  %m/%d
    
    section Core Setup
"""
            
            # 태스크별 섹션 구성
            current_date = start_date
            sections = {}
            
            for task in self.task_list:
                module = task.module
                if module not in sections:
                    sections[module] = []
                
                # 예상 소요 시간 계산 (복잡도 기반)
                duration_days = max(1, int(task.complexity))
                
                # 날짜 계산
                end_date = current_date + timedelta(days=duration_days)
                
                sections[module].append({
                    'task': task,
                    'start': current_date,
                    'end': end_date,
                    'duration': duration_days
                })
                
                current_date = end_date + timedelta(days=1)  # 1일 간격
            
            # 섹션별 출력
            for module, tasks in sections.items():
                gantt_content += f"\n    section {module.title()}\n"
                
                for task_info in tasks:
                    task = task_info['task']
                    start_str = task_info['start'].strftime('%Y-%m-%d')
                    duration = task_info['duration']
                    
                    # 태스크 상태 결정
                    status = "done" if task.complexity <= 1.0 else "active"
                    
                    # 라벨 구성
                    label = f"{task.id}: {task.title[:20]}{'...' if len(task.title) > 20 else ''}"
                    
                    gantt_content += f"    {label}     :{status}, {task.id.replace(':', '_')}, {start_str}, {duration}d\n"
            
            gantt_content += """```

## 복잡도 분석

| 복잡도 구간 | 태스크 수 | 색상 코드 | 설명 |
|------------|-----------|-----------|------|
| Low (0.0-1.0) | {low_count} | 🟢 | 단순한 작업 |
| Medium (1.0-2.0) | {medium_count} | 🟡 | 중간 복잡도 |
| High (2.0-3.0) | {high_count} | 🔴 | 복잡한 작업 |
| Critical (3.0+) | {critical_count} | 🟣 | 매우 복잡한 작업 |

## 임계 경로

{critical_path_section}

## 의존성 분석

{dependency_section}
"""
            
            # 복잡도 통계 계산
            low_count = sum(1 for t in self.task_list if t.complexity <= 1.0)
            medium_count = sum(1 for t in self.task_list if 1.0 < t.complexity <= 2.0)
            high_count = sum(1 for t in self.task_list if 2.0 < t.complexity <= 3.0)
            critical_count = sum(1 for t in self.task_list if t.complexity > 3.0)
            
            # 임계 경로 섹션
            critical_path = self._find_critical_path()
            critical_path_section = ""
            if critical_path:
                critical_path_section = "다음 태스크들이 임계 경로를 구성합니다:\n\n"
                for task_id in critical_path:
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        critical_path_section += f"- **{task.id}**: {task.title} (복잡도: {task.complexity:.2f})\n"
            else:
                critical_path_section = "현재 임계 경로가 식별되지 않았습니다."
            
            # 의존성 섹션
            dependency_section = "### 의존성 체인\n\n"
            for task in self.task_list:
                if task.deps:
                    deps_str = ", ".join(task.deps)
                    dependency_section += f"- **{task.id}** → {deps_str}\n"
            
            # 통계 값 치환
            gantt_content = gantt_content.format(
                low_count=low_count,
                medium_count=medium_count,
                high_count=high_count,
                critical_count=critical_count,
                critical_path_section=critical_path_section,
                dependency_section=dependency_section
            )
            
            # 파일 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(gantt_content)
            
            print(f"✅ Mermaid Gantt 차트 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Mermaid Gantt 차트 생성 실패: {e}")
            return False
    
    def generate_mermaid_flowchart(self, output_file: str = "tasks_flow.md"):
        """Mermaid Flowchart 생성"""
        print("🔄 Mermaid Flowchart 생성 중...")
        
        try:
            flowchart_content = """# 태스크 실행 플로우

```mermaid
flowchart TD
"""
            
            # 노드 정의
            for task in self.task_list:
                # 노드 스타일 결정
                if task.complexity >= 2.0:
                    style = "fill:#ff6b6b,stroke:#333,stroke-width:3px,color:#fff"
                elif task.complexity >= 1.5:
                    style = "fill:#f39c12,stroke:#333,stroke-width:2px,color:#fff"
                else:
                    style = "fill:#2ecc71,stroke:#333,stroke-width:1px,color:#fff"
                
                # 노드 라벨
                label = f"{task.id}\\n{task.title[:25]}{'...' if len(task.title) > 25 else ''}\\nC={task.complexity:.1f}"
                
                flowchart_content += f'    {task.id.replace(":", "_")}["{label}"]\n'
            
            # 엣지 정의 (의존성)
            flowchart_content += "\n"
            for task in self.task_list:
                for dep in task.deps:
                    if dep in self.tasks:
                        dep_node = dep.replace(":", "_")
                        task_node = task.id.replace(":", "_")
                        
                        # 임계 경로 강조
                        if task.complexity >= 2.0 or self.tasks[dep].complexity >= 2.0:
                            flowchart_content += f"    {dep_node} -->|critical| {task_node}\n"
                        else:
                            flowchart_content += f"    {dep_node} --> {task_node}\n"
            
            flowchart_content += """```

## 레전드

- 🟢 **녹색**: 낮은 복잡도 (≤ 1.5)
- 🟡 **주황**: 중간 복잡도 (1.5-2.0)  
- 🔴 **빨강**: 높은 복잡도 (≥ 2.0)
- **굵은 선**: 임계 경로

## 실행 순서

{execution_order}
"""
            
            # 실행 순서 생성 (토폴로지 순서)
            execution_order = ""
            sorted_tasks = sorted(self.task_list, key=lambda x: x.order or 0)
            
            for i, task in enumerate(sorted_tasks, 1):
                execution_order += f"{i}. **{task.id}**: {task.title} (복잡도: {task.complexity:.2f})\n"
            
            flowchart_content = flowchart_content.format(execution_order=execution_order)
            
            # 파일 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(flowchart_content)
            
            print(f"✅ Mermaid Flowchart 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Mermaid Flowchart 생성 실패: {e}")
            return False
    
    def generate_summary_report(self, output_file: str = "visualization_summary.md"):
        """시각화 요약 리포트 생성"""
        print("📋 시각화 요약 리포트 생성 중...")
        
        try:
            # 먼저 변수들을 계산
            # 복잡도 분포
            complexity_distribution = ""
            complexity_ranges = [
                (0.0, 1.0, "🟢 낮음"),
                (1.0, 2.0, "🟡 중간"),
                (2.0, 3.0, "🔴 높음"),
                (3.0, float('inf'), "🟣 매우 높음")
            ]
            
            for min_comp, max_comp, label in complexity_ranges:
                count = sum(1 for t in self.task_list if min_comp <= t.complexity < max_comp)
                percentage = (count / len(self.task_list)) * 100 if self.task_list else 0
                complexity_distribution += f"- {label}: {count}개 ({percentage:.1f}%)\n"
            
            # 모듈별 분포
            module_distribution = ""
            modules = {}
            for task in self.task_list:
                module = task.module
                if module not in modules:
                    modules[module] = {'count': 0, 'total_complexity': 0}
                modules[module]['count'] += 1
                modules[module]['total_complexity'] += task.complexity
            
            for module, stats in modules.items():
                avg_complexity = stats['total_complexity'] / stats['count']
                module_distribution += f"- **{module}**: {stats['count']}개 (평균 복잡도: {avg_complexity:.2f})\n"
            
            # 권장사항
            recommendations = ""
            high_complexity_tasks = [t for t in self.task_list if t.complexity >= 2.0]
            if high_complexity_tasks:
                recommendations += f"- **높은 복잡도 태스크 ({len(high_complexity_tasks)}개) 우선 처리**: "
                recommendations += ", ".join([t.id for t in high_complexity_tasks]) + "\n"
            
            independent_tasks = self._get_independent_tasks()
            if independent_tasks:
                recommendations += f"- **독립 태스크 병렬 실행**: {', '.join(independent_tasks)}\n"
            
            recommendations += "- **의존성 체인 최적화**: 병목 지점 식별 및 해결\n"
            recommendations += "- **리소스 할당**: 복잡도 기반 시간 및 인력 계획"
            
            # 이제 템플릿 생성
            report_content = f"""# DAG 시각화 요약 리포트

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
원본 파일: {self.input_file}

## 📊 태스크 통계

- **총 태스크 수**: {len(self.task_list)}개
- **모듈 수**: {len(set(t.module for t in self.task_list))}개
- **평균 복잡도**: {sum(t.complexity for t in self.task_list) / len(self.task_list):.2f}

### 복잡도 분포

{complexity_distribution}

### 모듈별 분포

{module_distribution}

## 🔗 의존성 분석

- **최대 의존성 깊이**: {self._get_max_dependency_depth()}
- **순환 의존성**: {self._detect_cycles()}
- **독립 태스크**: {len(self._get_independent_tasks())}개

## 📈 생성된 시각화 파일

- **Graphviz DAG**: `tasks_dag.svg`, `tasks_dag.png`
- **Mermaid Gantt**: `tasks_gantt.md`
- **Mermaid Flowchart**: `tasks_flow.md`
- **요약 리포트**: `{output_file}`

## 🚀 다음 단계

1. **Graphviz DAG** 확인: 병목 및 임계 경로 식별
2. **Mermaid Gantt** 확인: 일정 및 리소스 계획
3. **Mermaid Flowchart** 확인: 실행 순서 및 의존성
4. **우선순위 실행**: 복잡도 기반 단계별 실행

## 💡 권장사항

{recommendations}
"""
            
            
            # 파일 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"✅ 시각화 요약 리포트 생성 완료: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 시각화 요약 리포트 생성 실패: {e}")
            return False
    
    def _get_max_dependency_depth(self) -> int:
        """최대 의존성 깊이 계산"""
        def get_depth(task_id: str, visited: Set[str]) -> int:
            if task_id in visited:
                return 0  # 순환 참조 방지
            
            visited.add(task_id)
            max_depth = 0
            
            for dep in self.dependency_graph.get(task_id, []):
                depth = get_depth(dep, visited) + 1
                max_depth = max(max_depth, depth)
            
            visited.remove(task_id)
            return max_depth
        
        max_depth = 0
        for task in self.task_list:
            depth = get_depth(task.id, set())
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _detect_cycles(self) -> str:
        """순환 의존성 감지"""
        def has_cycle(task_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep in self.dependency_graph.get(task_id, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        visited = set()
        for task in self.task_list:
            if task.id not in visited:
                if has_cycle(task.id, visited, set()):
                    return "발견됨 ⚠️"
        
        return "없음 ✅"
    
    def _get_independent_tasks(self) -> List[str]:
        """독립 태스크 찾기 (의존성이 없는 태스크)"""
        independent = []
        for task in self.task_list:
            if not task.deps:
                independent.append(task.id)
        return independent

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='DAG 시각화 도구')
    parser.add_argument('--input', '-i', required=True, help='입력 파일 (tasks.reflected.json)')
    parser.add_argument('--format', '-f', choices=['graphviz', 'mermaid', 'both', 'all'], 
                       default='all', help='출력 형식')
    parser.add_argument('--output', '-o', help='출력 파일명 (확장자 제외)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ 입력 파일이 존재하지 않음: {args.input}")
        sys.exit(1)
    
    # DAG 시각화 도구 초기화
    visualizer = DAGVisualizer(args.input)
    visualizer.load_tasks()
    
    # 출력 형식에 따른 시각화 생성
    success_count = 0
    total_count = 0
    
    if args.format in ['graphviz', 'both', 'all']:
        total_count += 1
        output_file = args.output or "tasks_dag"
        if visualizer.generate_graphviz_dag(output_file):
            success_count += 1
    
    if args.format in ['mermaid', 'both', 'all']:
        total_count += 2
        if visualizer.generate_mermaid_gantt():
            success_count += 1
        if visualizer.generate_mermaid_flowchart():
            success_count += 1
    
    if args.format == 'all':
        total_count += 1
        if visualizer.generate_summary_report():
            success_count += 1
    
    # 결과 출력
    print(f"\n🎉 시각화 완료: {success_count}/{total_count}개 파일 생성 성공")
    
    if success_count == total_count:
        print("✅ 모든 시각화 파일이 성공적으로 생성되었습니다!")
    else:
        print("⚠️ 일부 파일 생성에 실패했습니다.")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
