import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서 찾기)
# 현재 파일의 디렉토리에서 상위 디렉토리(프로젝트 루트)로 이동
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

# .env 파일 로드 (프로젝트 루트 경로 명시)
load_dotenv(dotenv_path=env_path)

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
        # .env 파일 경로 확인
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        env_path = os.path.join(project_root, '.env')
        
        error_msg = "OPENAI_API_KEY가 설정되지 않았습니다.\n\n"
        if os.path.exists(env_path):
            error_msg += f"✅ .env 파일은 존재합니다: {env_path}\n"
            error_msg += "⚠️ .env 파일에 다음 형식으로 OPENAI_API_KEY를 추가해주세요:\n"
            error_msg += "   OPENAI_API_KEY=sk-your-api-key-here\n"
        else:
            error_msg += f"❌ .env 파일을 찾을 수 없습니다: {env_path}\n"
            error_msg += "📝 프로젝트 루트에 .env 파일을 생성하고 다음 내용을 추가해주세요:\n"
            error_msg += "   OPENAI_API_KEY=sk-your-api-key-here\n"
        
        error_msg += "\n💡 OpenAI API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다."
        raise ValueError(error_msg)
    
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
    """데이터베이스의 기록을 읽어서 통계 기반 종합 피드백에 사용할 데이터 문자열 반환"""
    try:
        from database import get_all_records, get_statistics
        from datetime import datetime, timedelta
        
        all_records = get_all_records()
        
        if not all_records:
            return "기록된 데이터가 없습니다."
        
        # 데이터 요약 정보 생성
        summary_lines = []
        summary_lines.append("=== 통계 기반 종합 분석 데이터 ===\n")
        
        # 전체 통계 정보
        stats = get_statistics()
        summary_lines.append("📊 전체 통계 요약:")
        summary_lines.append(f"  - 총 기록 수: {stats['total_records']}개")
        
        # 날짜별 통계
        dates = [r['date'] for r in all_records]
        unique_dates = len(set(dates))
        min_date = min(dates)
        max_date = max(dates)
        summary_lines.append(f"  - 기록된 날짜: {unique_dates}일")
        summary_lines.append(f"  - 기간: {min_date} ~ {max_date}")
        
        # 최근 7일 기록 수
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        recent_week_records = [r for r in all_records if r['date'] >= week_ago.isoformat()]
        summary_lines.append(f"  - 최근 7일 기록 수: {len(recent_week_records)}개")
        summary_lines.append("")
        
        # 카테고리별 상세 통계
        category_counts = {}
        category_times = {}
        category_avg_times = {}
        category_records_list = {}
        
        for record in all_records:
            cat = record['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            if cat not in category_records_list:
                category_records_list[cat] = []
            category_records_list[cat].append(record)
            
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
        
        # 카테고리별 평균 시간 계산
        for cat in category_counts:
            if category_counts[cat] > 0:
                category_avg_times[cat] = category_times.get(cat, 0) / category_counts[cat]
        
        summary_lines.append("📈 카테고리별 상세 통계:")
        for cat in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            cat_name = cat[0]
            count = cat[1]
            total_hours = category_times.get(cat_name, 0)
            avg_hours = category_avg_times.get(cat_name, 0)
            percentage = (count / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
            summary_lines.append(f"  - {cat_name}:")
            summary_lines.append(f"    * 기록 수: {count}회 ({percentage:.1f}%)")
            summary_lines.append(f"    * 총 시간: {total_hours:.1f}시간")
            summary_lines.append(f"    * 평균 시간: {avg_hours:.2f}시간/회")
        summary_lines.append("")
        
        # 시간대별 활동 패턴 분석
        hourly_counts = {}
        for record in all_records:
            try:
                hour = int(record['start_time'].split(':')[0])
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            except:
                pass
        
        if hourly_counts:
            summary_lines.append("⏰ 시간대별 활동 패턴:")
            # 가장 활발한 시간대
            most_active_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
            if most_active_hour is not None:
                summary_lines.append(f"  - 가장 활발한 시간대: {most_active_hour}시 ({hourly_counts[most_active_hour]}회)")
            # 시간대별 분포
            summary_lines.append("  - 시간대별 활동 분포:")
            for hour in sorted(hourly_counts.keys()):
                summary_lines.append(f"    * {hour}시: {hourly_counts[hour]}회")
            summary_lines.append("")
        
        # 일일 평균 기록 수
        if unique_dates > 0:
            avg_daily_records = stats['total_records'] / unique_dates
            summary_lines.append(f"📅 일일 평균 기록 수: {avg_daily_records:.1f}개/일")
            summary_lines.append("")
        
        # 최근 활동 패턴 (최근 7일)
        summary_lines.append("📋 최근 7일 활동 패턴:")
        recent_week_by_date = {}
        for record in recent_week_records:
            date = record['date']
            if date not in recent_week_by_date:
                recent_week_by_date[date] = []
            recent_week_by_date[date].append(record)
        
        for date in sorted(recent_week_by_date.keys(), reverse=True):
            day_records = recent_week_by_date[date]
            summary_lines.append(f"  - {date}: {len(day_records)}개 기록")
        summary_lines.append("")
        
        # 오늘의 활동
        today_str = today.isoformat()
        today_records = [r for r in all_records if r['date'] == today_str]
        if today_records:
            summary_lines.append(f"🌅 오늘({today_str}) 활동:")
            for record in today_records:
                try:
                    start = datetime.strptime(record['start_time'], "%H:%M")
                    end = datetime.strptime(record['end_time'], "%H:%M")
                    if end < start:
                        end += timedelta(days=1)
                    duration = (end - start).total_seconds() / 60  # 분 단위
                    summary_lines.append(f"  - {record['start_time']}-{record['end_time']} ({duration:.0f}분): {record['activity']} ({record['category']})")
                except:
                    summary_lines.append(f"  - {record['start_time']}-{record['end_time']}: {record['activity']} ({record['category']})")
            summary_lines.append("")
        
        # 활동 연속성 분석 (최근 기록의 일관성)
        if len(recent_week_records) > 0:
            consecutive_days = 0
            current_date = today
            for i in range(7):
                date_str = current_date.isoformat()
                if any(r['date'] == date_str for r in all_records):
                    consecutive_days += 1
                else:
                    break
                current_date -= timedelta(days=1)
            
            summary_lines.append(f"📊 활동 연속성: 최근 {consecutive_days}일 연속 기록")
            summary_lines.append("")
        
        return "\n".join(summary_lines)
    except Exception as e:
        print(f"데이터베이스 기록 로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return "데이터를 불러올 수 없습니다."

def get_realtime_feedback() -> dict:
    """
    데이터베이스 기록을 기반으로 실시간 피드백 생성
    
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
        
        # 통계 기반 종합 피드백 프롬프트
        feedback_prompt = """너는 사용자의 루틴 통계 데이터를 종합적으로 분석하여 하나의 통합된 피드백을 제공하는 AI 코치입니다.

**중요: 반드시 JSON 형식으로만 응답해야 합니다. 다른 텍스트나 설명은 포함하지 마세요.**

**말투 규칙:**
- 부드럽고 따뜻한 존댓말 사용
- 경어체로 작성 ("~하세요", "~하시면 됩니다", "~하시는 것이 좋겠습니다")
- 친근하지만 전문적인 톤 유지
- 긍정적인 피드백과 건설적인 제안을 균형있게 제공

**출력 형식:**
{
  "summary": "통계를 종합한 한 줄 요약 (50자 이내, 존댓말로 작성)",
  "feedbacks": [
    {
      "title": "종합 피드백 제목 (존댓말)",
      "description": "모든 통계를 종합한 구체적인 피드백 설명 (존댓말, 현실적이고 사실 기반)",
      "type": "positive"
    },
    {
      "title": "종합 피드백 제목 (존댓말)",
      "description": "모든 통계를 종합한 구체적인 피드백 설명 (존댓말, 현실적이고 사실 기반)",
      "type": "suggestion"
    },
    {
      "title": "종합 피드백 제목 (존댓말)",
      "description": "모든 통계를 종합한 구체적인 피드백 설명 (존댓말, 현실적이고 사실 기반)",
      "type": "neutral"
    }
  ],
  "timestamp": "YYYY-MM-DD HH:MM:SS 형식의 현재 시간"
}

**피드백 작성 규칙:**
1. 제공된 통계 데이터를 종합적으로 분석하여 하나의 통합된 피드백을 작성하세요
2. 통계별로 따로 피드백을 만들지 말고, 모든 통계를 종합하여 전체적인 패턴을 분석하세요
3. 다음 통계 요소들을 모두 고려하여 종합적으로 분석하세요:
   - 전체 기록 수와 기록 기간
   - 카테고리별 기록 수, 총 시간, 평균 시간, 비율
   - 시간대별 활동 패턴
   - 일일 평균 기록 수
   - 최근 활동 패턴과 연속성
   - 오늘의 활동
4. 긍정적인 점을 먼저 언급하고, 개선 가능한 점을 건설적으로 제안하세요
5. type은 "positive" (긍정적), "suggestion" (제안), "neutral" (중립적) 중 하나
6. 현실적이고 실행 가능한 피드백만 제공하세요
7. 통계 데이터에서 발견된 패턴과 트렌드를 종합적으로 분석하세요

**통계 종합 분석 시 고려사항:**
- 카테고리별 시간 분배의 균형 (수면, 식사, 일과, 운동, 취미, 기타)
- 가장 많은 시간을 투자하는 카테고리와 가장 적은 카테고리
- 시간대별 활동 패턴 (언제 가장 활발한지)
- 기록의 일관성과 연속성
- 일일 평균 기록 수와 최근 트렌드
- 오늘의 활동이 전체 패턴과 어떻게 일치하는지

**예시 (존댓말 톤, 통계 종합):**
- "전체 통계를 보니 꾸준히 기록을 남기고 계시네요! 카테고리별 시간 분배가 잘 이루어지고 있습니다."
- "카테고리별 통계를 종합해보니 운동 시간이 상대적으로 적은 편입니다. 주 3회 정도로 규칙적으로 늘려보시면 좋을 것 같습니다."
- "시간대별 패턴을 보니 오전 시간대에 활동이 집중되어 있네요. 저녁 시간에도 일부 활동을 분산시키면 더 균형잡힌 하루가 될 것 같습니다."

**규칙:**
1. JSON 형식만 출력 (마크다운, 코드 블록 없이)
2. summary는 50자 이내로 간결하게 (존댓말, 통계 종합 요약)
3. feedbacks 배열은 반드시 3개의 피드백 포함
4. type은 "positive", "suggestion", "neutral" 중 하나
5. description은 모든 통계를 종합한 실행 가능한 구체적인 피드백 (존댓말, 현실적)
6. timestamp는 ISO 8601 형식 또는 "YYYY-MM-DD HH:MM:SS" 형식
7. 모든 텍스트는 존댓말로 작성
8. 데이터에 없는 내용은 추측하지 말고, 실제 통계 데이터만 기반으로 종합 피드백
9. 통계별로 따로 피드백을 만들지 말고, 모든 통계를 하나로 종합하여 분석"""
        
        user_message = f"""사용자의 루틴 통계 데이터를 종합적으로 분석하여 하나의 통합된 피드백을 제공해주세요.

{routine_data_summary}

위 통계 데이터를 종합적으로 분석하여, 통계별로 따로 피드백을 만들지 말고 모든 통계를 하나로 통합하여 종합적인 피드백을 작성해주세요.
- 카테고리별 통계, 시간대별 패턴, 기록 연속성, 일일 평균 등을 모두 종합하여 분석하세요
- 긍정적인 점과 개선 가능한 점을 균형있게 존댓말(경어체)로 작성해주세요
- 통계 데이터에서 확인된 실제 패턴과 사실만을 바탕으로 종합 피드백하시고, 추측이나 이상적인 조언은 피해주세요"""
        
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
