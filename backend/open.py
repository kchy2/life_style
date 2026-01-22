import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프롬프트 파일에서 읽어오기
def load_ai_prompt():
    """AI 조언 프롬프트 로드"""
    try:
        with open("prompt.md", "r", encoding="utf-8") as f:
            content = f.read()
            # export const AI_ADVICE_PROMPT = `...` 형식에서 프롬프트 추출
            start = content.find("`") + 1
            end = content.rfind("`")
            if start > 0 and end > start:
                return content[start:end].strip()
    except:
        pass
    
    # 기본 프롬프트
    return """너는 웹 서비스에서 사용자에게 조언을 해주는 AI 코치야.

**중요: 반드시 JSON 형식으로만 응답해야 해. 다른 텍스트나 설명은 포함하지 마.**

**출력 형식:**
{
  "summary": "한 줄 요약 (50자 이내)",
  "advices": [
    {
      "title": "조언 제목",
      "description": "실행 가능한 구체적인 조언 설명",
      "priority": 1
    },
    {
      "title": "조언 제목",
      "description": "실행 가능한 구체적인 조언 설명",
      "priority": 2
    },
    {
      "title": "조언 제목",
      "description": "실행 가능한 구체적인 조언 설명",
      "priority": 3
    }
  ],
  "timestamp": "YYYY-MM-DD HH:MM:SS 형식의 현재 시간"
}

**규칙:**
1. JSON 형식만 출력 (마크다운, 코드 블록 없이)
2. summary는 50자 이내로 간결하게
3. advices 배열은 반드시 3개의 조언 포함
4. priority는 1(가장 중요)부터 3까지
5. description은 실행 가능한 구체적인 행동 지침
6. timestamp는 ISO 8601 형식 또는 "YYYY-MM-DD HH:MM:SS" 형식"""

# OpenAI 클라이언트 초기화
def get_openai_client():
    """OpenAI 클라이언트 생성 (.env 파일에서 API 키 읽기)"""
    # .env 파일에서 API 키 읽기
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # 환경 변수에서 직접 확인
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    
    return OpenAI(api_key=api_key)

def load_routine_data_for_advice() -> str:
    """routine_data_v2.csv 파일을 읽어서 조언에 사용할 데이터 문자열 반환"""
    try:
        csv_path = "routine_data_v2.csv"
        if not os.path.exists(csv_path):
            csv_path = os.path.join(os.path.dirname(__file__), "..", "routine_data_v2.csv")
        
        if os.path.exists(csv_path):
            import pandas as pd
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # 데이터 요약 정보 생성
            summary_lines = []
            summary_lines.append("=== 사용자 루틴 데이터 요약 ===\n")
            
            # 날짜별 통계
            date_counts = df['날짜'].value_counts().sort_index()
            summary_lines.append(f"기록된 날짜: {len(date_counts)}일")
            summary_lines.append(f"기간: {df['날짜'].min()} ~ {df['날짜'].max()}\n")
            
            # 카테고리별 통계
            category_stats = df['카테고리'].value_counts()
            summary_lines.append("카테고리별 활동 횟수:")
            for cat, count in category_stats.items():
                summary_lines.append(f"  - {cat}: {count}회")
            summary_lines.append("")
            
            # 전체 활동 데이터 (조언에 필요한 모든 정보)
            summary_lines.append("전체 활동 기록:")
            for idx, row in df.iterrows():
                memo_text = str(row['메모']).strip() if pd.notna(row['메모']) else ""
                if memo_text:
                    summary_lines.append(f"  [{row['날짜']}] {row['시간(시작-종료)']} | {row['활동명']} | {row['카테고리']} | 메모: {memo_text}")
                else:
                    summary_lines.append(f"  [{row['날짜']}] {row['시간(시작-종료)']} | {row['활동명']} | {row['카테고리']}")
            summary_lines.append("")
            
            # AI 개입 확인
            dynamic_count = df['메모'].astype(str).str.contains('[동적 루틴]', na=False).sum()
            micro_count = df['메모'].astype(str).str.contains('[마이크로 루틴]', na=False).sum()
            if dynamic_count > 0 or micro_count > 0:
                summary_lines.append(f"AI 개입 이력: 동적 루틴 {dynamic_count}회, 마이크로 루틴 {micro_count}회\n")
            
            # 수면 패턴 분석
            sleep_records = df[df['카테고리'] == '수면']
            if len(sleep_records) > 0:
                summary_lines.append("수면 패턴:")
                for idx, row in sleep_records.tail(3).iterrows():
                    summary_lines.append(f"  - {row['날짜']} {row['시간(시작-종료)']}: {row['메모'] if pd.notna(row['메모']) else ''}")
                summary_lines.append("")
            
            return "\n".join(summary_lines)
        else:
            return "CSV 파일을 찾을 수 없습니다."
    except Exception as e:
        print(f"CSV 데이터 로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return "데이터를 불러올 수 없습니다."

def load_database_records_for_feedback() -> str:
    """데이터베이스의 기록을 읽어서 실시간 피드백에 사용할 데이터 문자열 반환"""
    try:
        from database import get_all_records, get_statistics
        from datetime import datetime, timedelta
        
        all_records = get_all_records()
        
        if not all_records:
            return "기록된 데이터가 없습니다."
        
        # 데이터 요약 정보 생성
        summary_lines = []
        summary_lines.append("=== 사용자 루틴 데이터 요약 ===\n")
        
        # 날짜별 통계
        dates = [r['date'] for r in all_records]
        unique_dates = len(set(dates))
        min_date = min(dates)
        max_date = max(dates)
        summary_lines.append(f"기록된 날짜: {unique_dates}일")
        summary_lines.append(f"기간: {min_date} ~ {max_date}\n")
        
        # 카테고리별 통계
        category_counts = {}
        category_times = {}
        for record in all_records:
            cat = record['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # 시간 계산
            try:
                start = datetime.strptime(record['start_time'], "%H:%M")
                end = datetime.strptime(record['end_time'], "%H:%M")
                if end < start:
                    end += timedelta(days=1)
                duration = (end - start).total_seconds() / 3600  # 시간 단위
                category_times[cat] = category_times.get(cat, 0) + duration
            except:
                pass
        
        summary_lines.append("카테고리별 활동 횟수:")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            hours = category_times.get(cat, 0)
            summary_lines.append(f"  - {cat}: {count}회 (총 {hours:.1f}시간)")
        summary_lines.append("")
        
        # 최근 활동 (최근 10개)
        summary_lines.append("최근 활동 기록:")
        recent_records = sorted(all_records, key=lambda x: x['timestamp'], reverse=True)[:10]
        for record in recent_records:
            memo_text = record.get('memo', '').strip() if record.get('memo') else ""
            if memo_text:
                summary_lines.append(f"  [{record['date']}] {record['start_time']}-{record['end_time']} | {record['activity']} | {record['category']} | 메모: {memo_text}")
            else:
                summary_lines.append(f"  [{record['date']}] {record['start_time']}-{record['end_time']} | {record['activity']} | {record['category']}")
        summary_lines.append("")
        
        # 통계 정보
        stats = get_statistics()
        summary_lines.append("전체 통계:")
        summary_lines.append(f"  - 총 기록 수: {stats['total_records']}개")
        summary_lines.append("")
        
        # 오늘의 활동
        today = datetime.now().date().isoformat()
        today_records = [r for r in all_records if r['date'] == today]
        if today_records:
            summary_lines.append(f"오늘({today}) 활동:")
            for record in today_records:
                summary_lines.append(f"  - {record['start_time']}-{record['end_time']}: {record['activity']} ({record['category']})")
            summary_lines.append("")
        
        return "\n".join(summary_lines)
    except Exception as e:
        print(f"데이터베이스 기록 로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return "데이터를 불러올 수 없습니다."

def get_realtime_feedback(stat_type: str = "general") -> dict:
    """
    데이터베이스 기록을 기반으로 실시간 피드백 생성
    
    Args:
        stat_type: 통계 타입 ("date", "category", "time", "overall", "general")
            - "date": 날짜별 통계에 대한 피드백
            - "category": 카테고리별 통계에 대한 피드백
            - "time": 시간 분석에 대한 피드백
            - "overall": 전체 통계에 대한 피드백
            - "general": 일반적인 피드백 (기본값)
    
    Returns:
        dict: JSON 형식의 피드백 데이터
        {
            "summary": "한 줄 요약",
            "feedbacks": [
                {"title": "...", "description": "...", "type": "positive/neutral/suggestion"},
                ...
            ],
            "timestamp": "..."
        }
    """
    try:
        openai_client = get_openai_client()
        
        # 데이터베이스 기록 로드
        routine_data_summary = load_database_records_for_feedback()
        
        # 통계 타입별 프롬프트 커스터마이징
        stat_type_contexts = {
            "date": {
                "focus": "날짜별 기록 패턴과 일관성",
                "analysis_points": [
                    "최근 30일간의 기록 일관성",
                    "기록 빈도의 변화 추이",
                    "특정 요일이나 기간의 패턴",
                    "기록이 많은 날과 적은 날의 특징"
                ]
            },
            "category": {
                "focus": "카테고리별 시간 분배와 균형",
                "analysis_points": [
                    "카테고리별 시간 분배의 균형",
                    "가장 많은 시간을 투자하는 카테고리",
                    "부족한 카테고리와 개선 방안",
                    "카테고리별 활동의 다양성"
                ]
            },
            "time": {
                "focus": "시간대별 활동 패턴과 효율성",
                "analysis_points": [
                    "시간대별 활동 시작 패턴",
                    "가장 활발한 시간대",
                    "활동 시간의 효율성",
                    "카테고리별 평균 활동 시간의 적절성"
                ]
            },
            "overall": {
                "focus": "전체적인 루틴 패턴과 종합 평가",
                "analysis_points": [
                    "전체 기록의 일관성과 지속성",
                    "주간 활동 추이와 트렌드",
                    "총 활동 시간과 평균 활동 시간",
                    "전체적인 루틴의 균형과 개선점"
                ]
            },
            "general": {
                "focus": "전반적인 루틴 패턴",
                "analysis_points": [
                    "수면 시간과 패턴",
                    "카테고리별 시간 분배",
                    "활동의 연속성과 규칙성",
                    "오늘의 활동과 최근 패턴 비교"
                ]
            }
        }
        
        context = stat_type_contexts.get(stat_type, stat_type_contexts["general"])
        
        # 실시간 피드백 프롬프트
        feedback_prompt = f"""너는 사용자의 일상 루틴 데이터를 실시간으로 분석하여 즉각적인 피드백을 제공하는 AI 코치입니다.

**현재 분석 중인 통계 타입: {stat_type}**
**분석 초점: {context['focus']}**

**중요: 반드시 JSON 형식으로만 응답해야 합니다. 다른 텍스트나 설명은 포함하지 마세요.**

**말투 규칙:**
- 부드럽고 따뜻한 존댓말 사용
- 경어체로 작성 ("~하세요", "~하시면 됩니다", "~하시는 것이 좋겠습니다")
- 친근하지만 전문적인 톤 유지
- 긍정적인 피드백과 건설적인 제안을 균형있게 제공

**출력 형식:**
{
  "summary": "한 줄 요약 (50자 이내, 존댓말로 작성)",
  "feedbacks": [
    {
      "title": "피드백 제목 (존댓말)",
      "description": "구체적인 피드백 설명 (존댓말, 현실적이고 사실 기반)",
      "type": "positive"
    },
    {
      "title": "피드백 제목 (존댓말)",
      "description": "구체적인 피드백 설명 (존댓말, 현실적이고 사실 기반)",
      "type": "suggestion"
    },
    {
      "title": "피드백 제목 (존댓말)",
      "description": "구체적인 피드백 설명 (존댓말, 현실적이고 사실 기반)",
      "type": "neutral"
    }
  ],
  "timestamp": "YYYY-MM-DD HH:MM:SS 형식의 현재 시간"
}

**피드백 작성 규칙:**
1. 제공된 루틴 데이터를 반드시 기반으로 하여 피드백을 작성하세요
2. 데이터에서 확인된 실제 패턴, 시간 분배, 카테고리별 활동을 참고하세요
3. 긍정적인 점을 먼저 언급하고, 개선 가능한 점을 건설적으로 제안하세요
4. type은 "positive" (긍정적), "suggestion" (제안), "neutral" (중립적) 중 하나
5. 현실적이고 실행 가능한 피드백만 제공하세요
6. 최근 활동 패턴과 트렌드를 고려하세요

**데이터 분석 시 고려사항 (이 통계 타입에 특화된 분석):**
{chr(10).join(f"- {point}" for point in context['analysis_points'])}

**예시 (존댓말 톤):**
- "오늘도 꾸준히 기록을 남기고 계시네요! 일과 시간이 잘 유지되고 있습니다."
- "수면 패턴을 보니 규칙적으로 잘 지키고 계시는 것 같습니다. 이 패턴을 유지하시면 좋겠습니다."
- "운동 시간을 조금 더 늘려보시는 것은 어떨까요? 주 3회 정도로 규칙적으로 하시면 좋을 것 같습니다."

**규칙:**
1. JSON 형식만 출력 (마크다운, 코드 블록 없이)
2. summary는 50자 이내로 간결하게 (존댓말)
3. feedbacks 배열은 반드시 3개의 피드백 포함
4. type은 "positive", "suggestion", "neutral" 중 하나
5. description은 실행 가능한 구체적인 피드백 (존댓말, 현실적)
6. timestamp는 ISO 8601 형식 또는 "YYYY-MM-DD HH:MM:SS" 형식
7. 모든 텍스트는 존댓말로 작성
8. 데이터에 없는 내용은 추측하지 말고, 실제 데이터만 기반으로 피드백"""
        
        user_message = f"""사용자의 루틴 데이터를 분석하여 실시간 피드백을 제공해주세요.

**분석 초점: {context['focus']}**

{routine_data_summary}

위 루틴 데이터를 반드시 기반으로 하여, **{context['focus']}**에 특화된 피드백을 제공해주세요.
특히 다음 사항들을 중점적으로 분석해주세요:
{chr(10).join(f"- {point}" for point in context['analysis_points'])}

긍정적인 점과 개선 가능한 점을 균형있게 존댓말(경어체)로 작성해주세요. 
데이터에서 확인된 실제 패턴과 사실만을 바탕으로 피드백하시고, 추측이나 이상적인 조언은 피해주세요."""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": feedback_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        response_content = completion.choices[0].message.content
        
        # JSON 파싱
        try:
            result = json.loads(response_content)
            # timestamp 추가 (없는 경우)
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 응답
            return {
                "summary": "피드백을 생성할 수 없습니다.",
                "feedbacks": [
                    {
                        "title": "다시 시도",
                        "description": "잠시 후 다시 시도해주세요.",
                        "type": "neutral"
                    }
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    except Exception as e:
        error_str = str(e)
        # 사용량 한도 초과 오류 처리
        if "insufficient_quota" in error_str or "429" in error_str:
            return {
                "summary": "API 사용량 한도가 초과되었습니다.",
                "feedbacks": [
                    {
                        "title": "OpenAI 계정 확인",
                        "description": "OpenAI 계정의 결제 정보와 사용량 한도를 확인해주세요.",
                        "type": "neutral"
                    }
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # 오류 발생 시 기본 응답
        return {
            "summary": "피드백을 불러올 수 없습니다.",
            "feedbacks": [
                {
                    "title": "오류 발생",
                    "description": f"오류가 발생했습니다: {str(e)}",
                    "type": "neutral"
                }
            ],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def get_ai_advice(user_input: str) -> dict:
    """
    사용자 입력과 CSV 데이터를 기반으로 AI 조언 생성
    
    Args:
        user_input: 사용자 입력 텍스트
    
    Returns:
        dict: JSON 형식의 조언 데이터
        {
            "summary": "한 줄 요약",
            "advices": [
                {"title": "...", "description": "...", "priority": 1},
                ...
            ],
            "timestamp": "..."
        }
    """
    try:
        openai_client = get_openai_client()
        
        # CSV 데이터 기반 프롬프트 로드
        try:
            with open("ai_advice_with_data_prompt.md", "r", encoding="utf-8") as f:
                content = f.read()
                start = content.find("`") + 1
                end = content.rfind("`")
                if start > 0 and end > start:
                    ai_prompt = content[start:end].strip()
                else:
                    ai_prompt = load_ai_prompt()  # 기본 프롬프트 사용
        except:
            ai_prompt = load_ai_prompt()  # 기본 프롬프트 사용
        
        # CSV 데이터 로드
        routine_data_summary = load_routine_data_for_advice()
        
        # 사용자 입력과 데이터를 결합
        user_message = f"""사용자 질문/고민: {user_input}

{routine_data_summary}

위 루틴 데이터를 반드시 기반으로 하여, 사용자의 질문/고민에 대한 현실적이고 구체적인 조언을 존댓말(경어체)로 작성해주세요. 
데이터에서 확인된 실제 패턴과 사실만을 바탕으로 조언하시고, 추측이나 이상적인 조언은 피해주세요."""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ai_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        response_content = completion.choices[0].message.content
        
        # JSON 파싱
        try:
            result = json.loads(response_content)
            # timestamp 추가 (없는 경우)
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 응답
            return {
                "summary": "응답을 파싱할 수 없습니다.",
                "advices": [
                    {
                        "title": "다시 시도",
                        "description": "잠시 후 다시 시도해주세요.",
                        "priority": 1
                    }
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    except Exception as e:
        error_str = str(e)
        # 사용량 한도 초과 오류 처리
        if "insufficient_quota" in error_str or "429" in error_str:
            return {
                "summary": "API 사용량 한도가 초과되었습니다.",
                "advices": [
                    {
                        "title": "OpenAI 계정 확인",
                        "description": "OpenAI 계정의 결제 정보와 사용량 한도를 확인해주세요. https://platform.openai.com/usage 에서 확인하실 수 있습니다.",
                        "priority": 1
                    },
                    {
                        "title": "크레딧 충전",
                        "description": "OpenAI 계정에 크레딧이 부족할 수 있습니다. 결제 정보를 확인하고 필요시 크레딧을 충전해주세요.",
                        "priority": 2
                    },
                    {
                        "title": "잠시 후 재시도",
                        "description": "사용량 한도가 리셋될 때까지 기다리시거나, 다른 API 키를 사용해보세요.",
                        "priority": 3
                    }
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # 오류 발생 시 기본 응답
        return {
            "summary": f"오류가 발생했습니다: {str(e)}",
            "advices": [
                {
                    "title": "API 키 확인",
                    "description": "OPENAI_API_KEY가 올바르게 설정되었는지 확인해주세요.",
                    "priority": 1
                },
                {
                    "title": "네트워크 확인",
                    "description": "인터넷 연결을 확인해주세요.",
                    "priority": 2
                },
                {
                    "title": "다시 시도",
                    "description": "잠시 후 다시 시도해주세요.",
                    "priority": 3
                }
            ],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def load_routine_category_prompt():
    """루틴 카테고리 프롬프트 로드"""
    try:
        with open("routine_category_prompt.md", "r", encoding="utf-8") as f:
            content = f.read()
            # export const ROUTINE_CATEGORY_PROMPT = `...` 형식에서 프롬프트 추출
            # 첫 번째 백틱(`)과 마지막 백틱(`) 사이의 내용 추출
            start = content.find("`") + 1
            end = content.rfind("`")
            if start > 0 and end > start:
                prompt_text = content[start:end].strip()
                # 첫 줄이 export const로 시작하면 제거
                lines = prompt_text.split('\n')
                if lines and 'export const' in lines[0]:
                    prompt_text = '\n'.join(lines[1:])
                return prompt_text
    except Exception as e:
        print(f"프롬프트 로드 오류: {e}")
        pass
    
    # 기본 프롬프트
    return """너는 사용자의 일상 루틴을 분석하고 적절한 카테고리를 제안하는 AI 어시스턴트야.

**중요: 반드시 JSON 형식으로만 응답해야 해. 다른 텍스트나 설명은 포함하지 마.**

**출력 형식:**
{
  "suggested_category": "제안된 카테고리명",
  "category_description": "카테고리 설명 (50자 이내)",
  "alternative_categories": [
    {"name": "대안 카테고리", "reason": "이유 설명"}
  ],
  "routines": [
    {"name": "제안 루틴명", "description": "루틴 설명", "time_estimate": "예상 소요 시간"}
  ],
  "timestamp": "YYYY-MM-DD HH:MM:SS 형식의 현재 시간"
}"""

def get_routine_category_suggestion(user_input: str) -> dict:
    """
    사용자 입력에 대한 루틴 카테고리 제안 생성
    
    Args:
        user_input: 사용자가 입력한 활동/루틴 내용
    
    Returns:
        dict: JSON 형식의 카테고리 제안 데이터
    """
    try:
        openai_client = get_openai_client()
        category_prompt = load_routine_category_prompt()
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": category_prompt},
                {"role": "user", "content": f"사용자가 입력한 활동: {user_input}\n\n이 활동에 적합한 카테고리와 관련 루틴을 제안해주세요."}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        response_content = completion.choices[0].message.content
        
        # JSON 파싱
        try:
            result = json.loads(response_content)
            # timestamp 추가 (없는 경우)
            if "timestamp" not in result:
                result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 응답
            return {
                "suggested_category": "기타",
                "category_description": "카테고리를 자동으로 분류할 수 없습니다.",
                "alternative_categories": [
                    {"name": "식사", "reason": "일반적인 식사 활동으로 분류됩니다"}
                ],
                "routines": [
                    {
                        "name": user_input,
                        "description": "사용자가 입력한 활동",
                        "time_estimate": "30분"
                    }
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    except Exception as e:
        # 오류 발생 시 기본 응답
        return {
            "suggested_category": "기타",
            "category_description": "오류가 발생했습니다.",
            "alternative_categories": [
                {"name": "식사", "reason": "기본 카테고리"}
            ],
            "routines": [
                {
                    "name": user_input if user_input else "새 루틴",
                    "description": "사용자가 입력한 활동",
                    "time_estimate": "30분"
                }
            ],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
