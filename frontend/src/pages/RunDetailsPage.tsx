import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, CheckCircle, XCircle, Clock, Globe, 
  Download, FileText, Brain, ShieldAlert, Loader2, Play
} from 'lucide-react';
import toast from 'react-hot-toast';
import { testRunsAPI } from '../api';
import type { TestRun, TestResult, TestRunProgress } from '../types';
import AppLayout from '../components/AppLayout';

export default function RunDetailsPage() {
  const { id } = useParams<{ id: string }>();
  
  const [run, setRun] = useState<TestRun | null>(null);
  const [progress, setProgress] = useState<TestRunProgress | null>(null);
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    
    const fetchDetails = async () => {
      try {
        const [runRes, progRes, resRes] = await Promise.all([
          testRunsAPI.get(id),
          testRunsAPI.status(id),
          testRunsAPI.results(id)
        ]);
        
        setRun(runRes.data);
        setProgress(progRes.data);
        setResults(resRes.data);
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to load run details');
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
    
    // Connect WebSocket if run is running
    let ws: WebSocket | null = null;
    if (run?.status === 'PENDING' || run?.status === 'RUNNING') {
      const token = localStorage.getItem('auth-storage') ? JSON.parse(localStorage.getItem('auth-storage')!).state.token : null;
      if (token) {
        // Derive WS URL from current host, fallback to localhost:8000 for dev
        const wsUrl = import.meta.env.VITE_API_URL 
          ? import.meta.env.VITE_API_URL.replace('http', 'ws') + `/api/v1/runs/${id}/ws?token=${token}`
          : `ws://localhost:8000/api/v1/runs/${id}/ws?token=${token}`;

        ws = new WebSocket(wsUrl);
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.run_finished) {
            // Re-fetch all data once completed
            fetchDetails();
            return;
          }

          setProgress(prev => {
            if (!prev) return prev;
            const passedInc = data.passed ? 1 : 0;
            const failedInc = data.passed ? 0 : 1;
            const newCompleted = prev.completed_cases + 1;
            const total = prev.total_cases > 0 ? prev.total_cases : Math.max(1, newCompleted);
            
            return {
              ...prev,
              completed_cases: newCompleted,
              passed_cases: prev.passed_cases + passedInc,
              failed_cases: prev.failed_cases + failedInc,
              progress_pct: Math.min(100, Math.round((newCompleted / total) * 100))
            };
          });
        };
      }
    }
    
    return () => {
      if (ws) ws.close();
    };
  }, [id, run?.status]);

  if (loading) {
    return (
      <AppLayout title="Loading Run...">
        <div className="flex flex-col items-center justify-center min-h-[50vh]">
          <Loader2 className="animate-spin text-[var(--color-primary)] mb-4" size={40} />
          <p className="text-[var(--color-text-muted)]">Loading test run details...</p>
        </div>
      </AppLayout>
    );
  }

  if (error || !run) {
    return (
      <AppLayout title="Run Not Found">
        <div className="p-6 max-w-6xl mx-auto w-full">
          <div className="card border-red-200 bg-red-50 text-red-600">
            {error || 'Test run not found'}
          </div>
        </div>
      </AppLayout>
    );
  }

  const isRunning = run.status === 'PENDING' || run.status === 'RUNNING';

  const handleExport = async (format: 'html' | 'json') => {
    try {
      const toastId = toast.loading(`Exporting ${format.toUpperCase()} report...`);
      const res = format === 'html' 
        ? await testRunsAPI.exportReportHtml(run.id)
        : await testRunsAPI.exportReportJson(run.id);
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `specguard-report-${run.id}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      toast.success('Report exported successfully!', { id: toastId });
    } catch (err) {
      toast.error('Failed to export report');
    }
  };

  return (
    <AppLayout title={`Test Run ${run.id.slice(0, 8)}`}>
      <div className="page-container p-6 max-w-6xl mx-auto w-full">
        {/* Header */}
      <div className="mb-6">
        <Link to="/runs" className="inline-flex items-center text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] mb-4 transition-colors">
          <ArrowLeft size={16} className="mr-1" /> Back to Test Runs
        </Link>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              Test Run Details
              <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${
                run.status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
                run.status === 'FAILED' ? 'bg-red-100 text-red-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {run.status}
              </span>
            </h1>
            <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-[var(--color-text-muted)]">
              <span className="flex items-center gap-1.5"><Globe size={16} /> {run.base_url}</span>
              <span className="flex items-center gap-1.5"><Clock size={16} /> {new Date(run.created_at).toLocaleString()}</span>
              <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded">ID: {run.id}</span>
            </div>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={() => handleExport('json')}
              className={`btn btn-secondary ${isRunning ? 'opacity-50 pointer-events-none' : ''}`}
              disabled={isRunning}
            >
              <FileText size={18} />
              JSON
            </button>
            <button 
              onClick={() => handleExport('html')}
              className={`btn btn-primary ${isRunning ? 'opacity-50 pointer-events-none' : ''}`}
              disabled={isRunning}
            >
              <Download size={18} />
              Export HTML Report
            </button>
          </div>
        </div>
      </div>

      {/* Progress & Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card p-5 md:col-span-4">
          <div className="flex justify-between text-sm font-semibold mb-2">
            <span>Overall Progress</span>
            <span>{progress?.progress_pct ?? 0}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${run.status === 'FAILED' ? 'bg-red-500' : 'bg-[var(--color-primary)]'}`}
              style={{ width: `${progress?.progress_pct ?? 0}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-[var(--color-text-muted)] mt-2">
            <span>{progress?.completed_cases ?? 0} of {progress?.total_cases ?? 0} cases completed</span>
          </div>
        </div>

        <div className="card p-5 border-l-4 border-l-green-500">
          <div className="text-[var(--color-text-muted)] text-sm mb-1 font-medium">Passed</div>
          <div className="text-3xl font-bold text-green-600 flex items-center gap-2">
            {progress?.passed_cases ?? 0} <CheckCircle className="opacity-20" />
          </div>
        </div>
        
        <div className="card p-5 border-l-4 border-l-red-500">
          <div className="text-[var(--color-text-muted)] text-sm mb-1 font-medium">Failed</div>
          <div className="text-3xl font-bold text-red-600 flex items-center gap-2">
            {progress?.failed_cases ?? 0} <XCircle className="opacity-20" />
          </div>
        </div>

        <div className="card p-5 md:col-span-2 flex flex-col justify-center">
          <div className="text-[var(--color-text-muted)] text-sm mb-1 font-medium">Duration</div>
          <div className="text-xl font-bold">
            {run.completed_at && run.started_at 
              ? `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
              : isRunning ? 'Running...' : 'N/A'
            }
          </div>
        </div>
      </div>

      {/* Results List */}
      <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
        <Play size={20} className="text-[var(--color-primary)]" />
        Test Execution Results
      </h2>
      
      {results.length === 0 ? (
        <div className="card text-center p-12 text-[var(--color-text-muted)]">
          <p>No results available yet.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {results.map((res) => (
            <div key={res.id} className="card p-0 overflow-hidden">
              <div className={`p-4 border-l-4 flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                res.passed ? 'border-l-green-500' : 'border-l-red-500'
              }`}>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded uppercase ${
                      res.passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {res.status}
                    </span>
                    <span className="font-mono text-sm">{res.test_case_id}</span>
                  </div>
                  <div className="text-sm text-[var(--color-text-muted)] flex items-center gap-4">
                    <span>Status: {res.actual_status_code || 'N/A'}</span>
                    <span>Latency: {res.latency_ms}ms</span>
                  </div>
                </div>

                {/* AI Failure Analysis (if present) */}
                {res.ai_failure_analysis && (
                  <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 md:w-1/2">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain size={16} className="text-purple-600" />
                      <span className="font-semibold text-sm text-purple-900">AI Analysis</span>
                      {Boolean(res.ai_failure_analysis.is_security_concern) && (
                        <span className="flex items-center gap-1 text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-bold ml-auto">
                          <ShieldAlert size={12} /> SECURITY
                        </span>
                      )}
                    </div>
                    <p className="text-sm mb-2 text-slate-700">
                      <strong>Root Cause:</strong> {String(res.ai_failure_analysis.root_cause)}
                    </p>
                    <p className="text-sm text-slate-700">
                      <strong>Fix:</strong> {String(res.ai_failure_analysis.suggested_fix)}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      </div>
    </AppLayout>
  );
}
