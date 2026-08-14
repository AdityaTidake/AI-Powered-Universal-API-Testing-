import { useEffect, useState } from 'react';
import { Shield, Plus, Users, Trash2, Loader2, UserPlus, ChevronLeft, ChevronRight } from 'lucide-react';
import { useOrgStore } from '../store/orgStore';
import { useAuthStore } from '../store/authStore';
import toast from 'react-hot-toast';
import AppLayout from '../components/AppLayout';

export default function OrgsPage() {
  const { user } = useAuthStore();
  const {
    orgs, loading, fetchOrgs, createOrg, deleteOrg, addMember, removeMember
  } = useOrgStore();

  const [isCreating, setIsCreating] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [newMemberId, setNewMemberId] = useState('');

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const totalItems = orgs.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentOrgs = orgs.slice(startIndex, startIndex + itemsPerPage);

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    try {
      await createOrg({ name: newOrgName });
      setNewOrgName('');
      setIsCreating(false);
      toast.success('Organization created!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to create organization');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this organization?')) return;
    try {
      await deleteOrg(id);
      toast.success('Organization deleted!');
      if (selectedOrgId === id) setSelectedOrgId(null);
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete organization');
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemberId.trim() || !selectedOrgId) return;
    try {
      await addMember(selectedOrgId, { user_id: newMemberId });
      setNewMemberId('');
      toast.success('Member added!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to add member');
    }
  };

  const handleRemoveMember = async (orgId: string, memberId: string) => {
    if (!window.confirm('Remove this member?')) return;
    try {
      await removeMember(orgId, memberId);
      toast.success('Member removed!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove member');
    }
  };

  const selectedOrg = orgs.find(o => o.id === selectedOrgId);

  return (
    <AppLayout title="Organizations">
      <div className="page-container p-6 max-w-6xl mx-auto w-full">
        <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1">Organizations</h1>
          <p className="text-[var(--color-text-muted)]">Manage your teams and workspaces</p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsCreating(true)}>
          <Plus size={18} />
          New Organization
        </button>
      </div>

      {isCreating && (
        <div className="card mb-8">
          <h3 className="font-semibold mb-4">Create Organization</h3>
          <form onSubmit={handleCreate} className="flex gap-4">
            <input
              type="text"
              className="input flex-1"
              placeholder="Organization Name"
              value={newOrgName}
              onChange={e => setNewOrgName(e.target.value)}
              autoFocus
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" size={18} /> : 'Create'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setIsCreating(false)}>
              Cancel
            </button>
          </form>
        </div>
      )}

      {loading && !orgs.length ? (
        <div className="flex justify-center p-12">
          <Loader2 className="animate-spin text-gray-400" size={32} />
        </div>
      ) : orgs.length === 0 ? (
        <div className="card text-center p-12 text-[var(--color-text-muted)]">
          <Shield size={48} className="mx-auto mb-4 opacity-20" />
          <p className="mb-4">You are not a member of any organizations yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Org List */}
          <div className="md:col-span-1 flex flex-col gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
              Your Organizations
            </h3>
            {currentOrgs.map(org => (
              <div 
                key={org.id}
                className={`card p-4 cursor-pointer transition-all hover:border-[var(--color-primary)] ${
                  selectedOrgId === org.id ? 'border-[var(--color-primary)] ring-1 ring-[var(--color-primary)]' : ''
                }`}
                onClick={() => setSelectedOrgId(org.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded bg-[var(--color-primary)]/10 text-[var(--color-primary)] flex items-center justify-center font-bold">
                      {org.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold">{org.name}</div>
                      <div className="text-xs text-[var(--color-text-muted)] mt-1">
                        {org.member_ids.length} Member(s)
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex justify-between items-center mt-2">
                <button 
                  className="btn btn-ghost btn-sm px-2"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(p => p - 1)}
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="text-xs font-medium text-[var(--color-text-muted)]">
                  Page {currentPage} of {totalPages}
                </span>
                <button 
                  className="btn btn-ghost btn-sm px-2"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(p => p + 1)}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </div>

          {/* Org Details */}
          <div className="md:col-span-2">
            {selectedOrg ? (
              <div className="card h-full">
                <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-4 mb-6">
                  <div>
                    <h2 className="text-xl font-bold">{selectedOrg.name}</h2>
                    <p className="text-sm text-[var(--color-text-muted)] mt-1">
                      Created on {new Date(selectedOrg.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {selectedOrg.owner_id === user?.id && (
                    <button 
                      className="btn btn-ghost text-red-500 hover:bg-red-50"
                      onClick={() => handleDelete(selectedOrg.id)}
                      title="Delete Organization"
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>

                <div className="mb-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Users size={18} className="text-[var(--color-primary)]" />
                    Members
                  </h3>
                  
                  {selectedOrg.owner_id === user?.id && (
                    <form onSubmit={handleAddMember} className="flex gap-3 mb-6 bg-slate-50 p-4 rounded-lg">
                      <input
                        type="text"
                        className="input flex-1 bg-white"
                        placeholder="User ID to add..."
                        value={newMemberId}
                        onChange={e => setNewMemberId(e.target.value)}
                      />
                      <button type="submit" className="btn btn-primary shadow-sm" disabled={loading}>
                        <UserPlus size={18} />
                        Add Member
                      </button>
                    </form>
                  )}

                  <div className="flex flex-col gap-3">
                    {selectedOrg.member_ids.map(mId => (
                      <div key={mId} className="flex items-center justify-between p-3 rounded border border-[var(--color-border)]">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs text-slate-500 font-medium">
                            {mId === selectedOrg.owner_id ? 'OW' : 'MB'}
                          </div>
                          <div>
                            <div className="text-sm font-medium font-mono">{mId}</div>
                            {mId === selectedOrg.owner_id && (
                              <span className="text-[10px] uppercase font-bold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded mt-1 inline-block">
                                Owner
                              </span>
                            )}
                          </div>
                        </div>
                        {selectedOrg.owner_id === user?.id && mId !== selectedOrg.owner_id && (
                          <button 
                            className="btn btn-ghost btn-sm text-red-500"
                            onClick={() => handleRemoveMember(selectedOrg.id, mId)}
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            ) : (
              <div className="card h-full flex items-center justify-center text-[var(--color-text-muted)] border-dashed">
                Select an organization to view details
              </div>
            )}
          </div>
        </div>
      )}
      </div>
    </AppLayout>
  );
}
