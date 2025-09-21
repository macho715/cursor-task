#!/usr/bin/env python3
"""
Shrimp MCP 대체 로컬 리플렉터
의존성 분석 및 복잡도 계산을 수행합니다.

사용법:
    python tasks_reflect.py --in tasks.json --out tasks.reflected.json --report report.md
"""

import json
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

class TaskReflector:
    """태스크 의존성 분석 및 복잡도 계산기"""
    
    def __init__(self):
        # 타입별 기본 복잡도
        self.type_complexity = {
            'doc': 0.8,
            'cli': 0.9, 
            'config': 0.9,
            'code': 1.0,
            'ide': 1.0,
            'mcp': 1.2,
            'test': 1.1
        }
        
        # 제목 키워드별 복잡도 보너스
        self.title_bonus = {
            'complex': 0.3,
            'advanced': 0.2,
            'integration': 0.2,
            'optimization': 0.2,
            'validation': 0.1,
            'analysis': 0.1,
            'reflection': 0.1,
            'management': 0.1
        }
    
    def load_tasks(self, filepath: str) -> Dict:
        """태스크 JSON 파일 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다: {filepath}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"오류: JSON 파싱 실패: {e}")
            sys.exit(1)
    
    def detect_cycles(self, tasks: List[Dict]) -> List[List[str]]:
        """순환 의존성 감지 (DFS 기반)"""
        graph = {}
        for task in tasks:
            graph[task['id']] = task.get('deps', [])
        
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            if node in rec_stack:
                # 순환 발견
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            
            rec_stack.remove(node)
            path.pop()
        
        for task_id in graph:
            if task_id not in visited:
                dfs(task_id)
        
        return cycles
    
    def topological_sort(self, tasks: List[Dict]) -> Tuple[List[str], List[str]]:
        """토폴로지 정렬 (Kahn 알고리즘)"""
        # 그래프 구성
        graph = {}
        in_degree = {}
        
        for task in tasks:
            task_id = task['id']
            deps = task.get('deps', [])
            graph[task_id] = deps
            in_degree[task_id] = len(deps)
        
        # Kahn 알고리즘
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # 의존하는 태스크들의 in_degree 감소
            for task_id, deps in graph.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        # 순환 의존성 확인
        if len(result) != len(tasks):
            remaining = set(task['id'] for task in tasks) - set(result)
            return result, list(remaining)
        
        return result, []
    
    def calculate_complexity(self, task: Dict, all_tasks: List[Dict]) -> float:
        """복잡도 계산"""
        # 기본 복잡도 (타입별)
        task_type = task.get('type', 'code')
        base_complexity = self.type_complexity.get(task_type, 1.0)
        
        # 의존성 복잡도 (0.2 * 의존성 수)
        deps_count = len(task.get('deps', []))
        deps_complexity = 0.2 * deps_count
        
        # 의존자 복잡도 (0.1 * 이 태스크에 의존하는 태스크 수)
        dependents = sum(1 for t in all_tasks if task['id'] in t.get('deps', []))
        dependents_complexity = 0.1 * dependents
        
        # 제목 키워드 보너스
        title = task.get('title', '').lower()
        title_bonus = sum(bonus for keyword, bonus in self.title_bonus.items() 
                         if keyword in title)
        
        # 최종 복잡도 계산
        total_complexity = base_complexity + deps_complexity + dependents_complexity + title_bonus
        
        # 0.8 ~ 3.0 범위로 클램프
        return max(0.8, min(3.0, total_complexity))
    
    def reflect_tasks(self, tasks_data: Dict) -> Dict:
        """태스크 리플렉션 수행"""
        tasks = tasks_data.get('tasks', [])
        
        # 순환 의존성 감지
        cycles = self.detect_cycles(tasks)
        if cycles:
            print(f"경고: 순환 의존성 발견: {cycles}")
        
        # 토폴로지 정렬
        topo_order, remaining = self.topological_sort(tasks)
        if remaining:
            print(f"경고: 순환 의존성으로 인해 정렬되지 않은 태스크: {remaining}")
        
        # 복잡도 계산 및 순서 적용
        reflected_tasks = []
        for i, task_id in enumerate(topo_order):
            task = next(t for t in tasks if t['id'] == task_id)
            
            # 복잡도 계산
            complexity = self.calculate_complexity(task, tasks)
            
            # 리플렉션된 태스크 생성
            reflected_task = task.copy()
            reflected_task['order'] = i
            reflected_task['complexity'] = round(complexity, 2)
            
            reflected_tasks.append(reflected_task)
        
        # 메타데이터 업데이트
        reflected_data = tasks_data.copy()
        reflected_data['tasks'] = reflected_tasks
        reflected_data['meta'] = reflected_data.get('meta', {})
        reflected_data['meta']['reflected_at'] = datetime.now().isoformat()
        reflected_data['meta']['topo_order'] = topo_order
        reflected_data['meta']['cycles_detected'] = len(cycles)
        
        return reflected_data
    
    def generate_report(self, original_data: Dict, reflected_data: Dict, report_path: str):
        """리플렉션 리포트 생성"""
        tasks = reflected_data.get('tasks', [])
        
        # 통계 계산
        total_tasks = len(tasks)
        avg_complexity = sum(t['complexity'] for t in tasks) / total_tasks if total_tasks > 0 else 0
        max_complexity = max((t['complexity'] for t in tasks), default=0)
        min_complexity = min((t['complexity'] for t in tasks), default=0)
        
        # 타입별 통계
        type_stats = defaultdict(list)
        for task in tasks:
            type_stats[task.get('type', 'unknown')].append(task['complexity'])
        
        # 모듈별 통계
        module_stats = defaultdict(list)
        for task in tasks:
            module = task.get('module', 'unknown')
            module_stats[module].append(task['complexity'])
        
        # 리포트 생성
        report = f"""# 태스크 리플렉션 리포트

## 📊 **리플렉션 요약**
- **생성일**: {reflected_data['meta'].get('reflected_at', 'N/A')}
        - **원본 파일**: {original_data.get('meta', {}).get('source', 'N/A')}
- **태스크 수**: {total_tasks}개
- **순환 의존성**: {reflected_data['meta'].get('cycles_detected', 0)}개 발견

## 📈 **복잡도 통계**
- **평균 복잡도**: {avg_complexity:.2f}
- **최대 복잡도**: {max_complexity:.2f}
- **최소 복잡도**: {min_complexity:.2f}

## 🔗 **실행 순서 (토폴로지 정렬)**
"""
        
        for i, task in enumerate(tasks):
            report += f"{i+1}. **{task['id']}** (복잡도: {task['complexity']})\n"
            report += f"   - 제목: {task.get('title', 'N/A')}\n"
            report += f"   - 타입: {task.get('type', 'N/A')}\n"
            report += f"   - 모듈: {task.get('module', 'N/A')}\n"
            report += f"   - 의존성: {len(task.get('deps', []))}개\n"
            report += "\n"
        
        # 타입별 통계
        report += "\n## 📋 **타입별 복잡도 분석**\n\n"
        for task_type, complexities in type_stats.items():
            avg_comp = sum(complexities) / len(complexities)
            report += f"- **{task_type}**: 평균 {avg_comp:.2f} (n={len(complexities)})\n"
        
        # 모듈별 통계
        report += "\n## 🏗️ **모듈별 복잡도 분석**\n\n"
        for module, complexities in module_stats.items():
            avg_comp = sum(complexities) / len(complexities)
            report += f"- **{module}**: 평균 {avg_comp:.2f} (n={len(complexities)})\n"
        
        # 복잡도 순위
        report += "\n## 🎯 **복잡도 순위 (높은 순)**\n\n"
        sorted_tasks = sorted(tasks, key=lambda x: x['complexity'], reverse=True)
        for i, task in enumerate(sorted_tasks[:5]):
            report += f"{i+1}. **{task['id']}**: {task['complexity']}\n"
        
        report += f"\n---\n*리플렉션 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        # 리포트 저장
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"리포트 생성 완료: {report_path}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='태스크 의존성 분석 및 복잡도 계산')
    parser.add_argument('--in', dest='input_file', required=True, help='입력 JSON 파일')
    parser.add_argument('--out', dest='output_file', required=True, help='출력 JSON 파일')
    parser.add_argument('--report', dest='report_file', required=True, help='리포트 파일')
    
    args = parser.parse_args()
    
    # 리플렉터 초기화
    reflector = TaskReflector()
    
    # 태스크 로드
    print(f"태스크 로드 중: {args.input_file}")
    tasks_data = reflector.load_tasks(args.input_file)
    
    # 리플렉션 수행
    print("리플렉션 수행 중...")
    reflected_data = reflector.reflect_tasks(tasks_data)
    
    # 결과 저장
    print(f"결과 저장 중: {args.output_file}")
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(reflected_data, f, indent=2, ensure_ascii=False)
    
    # 리포트 생성
    print(f"리포트 생성 중: {args.report_file}")
    reflector.generate_report(tasks_data, reflected_data, args.report_file)
    
    print("리플렉션 완료!")

if __name__ == '__main__':
    main()
