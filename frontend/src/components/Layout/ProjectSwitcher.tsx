import { PlusOutlined, SettingOutlined } from '@ant-design/icons';
import {
  Button,
  Divider,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  message,
} from 'antd';
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { useProject } from '@/contexts/ProjectContext';
import type { Project } from '@/types/project';
import { projectsApi } from '@/services/api/projects';
import type { ProjectConfigUpdatePayload } from '@/services/api/projects';
import {
  DEFAULT_PROJECT_ID,
  isValidProjectId,
  normalizeProjectId,
} from '@/utils/projects';

const formatProjectLabel = (project: Project, t: (key: string) => string) => {
  if (project.name) {
    return project.name === project.id
      ? project.name
      : `${project.name} (${project.id})`;
  }
  return project.id === DEFAULT_PROJECT_ID ? t('projects.default') : project.id;
};

const ProjectSwitcher = () => {
  const {
    projects,
    currentProjectId,
    setCurrentProjectId,
    addProject,
    removeProject,
  } = useProject();
  const { t } = useI18n();
  const [createOpen, setCreateOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [configLoading, setConfigLoading] = useState(false);
  const [postgresHasPassword, setPostgresHasPassword] = useState(false);
  const [neo4jHasPassword, setNeo4jHasPassword] = useState(false);
  const [createForm] = Form.useForm();
  const [configForm] = Form.useForm();

  const options = projects.map((project) => ({
    value: project.id,
    label: formatProjectLabel(project, t),
  }));

  const normalizePostgresPayload = (
    postgres?: {
      host?: string;
      port?: number;
      user?: string;
      password?: string;
      database?: string;
      sslmode?: string;
      schema?: string;
    }
  ) => {
    if (!postgres) return undefined;
    const normalized = { ...postgres };
    if (normalized.host) normalized.host = normalized.host.trim();
    if (normalized.user) normalized.user = normalized.user.trim();
    if (normalized.database) normalized.database = normalized.database.trim();
    if (normalized.password) normalized.password = normalized.password.trim();
    if (!normalized.password) delete normalized.password;
    if (normalized.sslmode !== undefined) {
      normalized.sslmode = normalized.sslmode.trim();
      if (!normalized.sslmode) delete normalized.sslmode;
    }
    if (normalized.schema !== undefined) {
      normalized.schema = normalized.schema.trim();
      if (!normalized.schema) delete normalized.schema;
    }
    return normalized;
  };

  const normalizeNeo4jPayload = (
    neo4j?: { uri?: string; user?: string; password?: string }
  ) => {
    if (!neo4j) return undefined;
    const normalized = { ...neo4j };
    if (normalized.uri) normalized.uri = normalized.uri.trim();
    if (normalized.user) normalized.user = normalized.user.trim();
    if (normalized.password) normalized.password = normalized.password.trim();
    if (!normalized.password) delete normalized.password;
    return normalized;
  };

  const handleCreate = async () => {
    let values: {
      name?: string;
      id?: string;
      postgres?: {
        host?: string;
        port?: number;
        user?: string;
        password?: string;
        database?: string;
        sslmode?: string;
        schema?: string;
      };
      neo4j?: { uri?: string; user?: string; password?: string };
    };
    try {
      values = await createForm.validateFields();
    } catch {
      return;
    }
    const name = typeof values.name === 'string' ? values.name.trim() : '';
    const rawId = typeof values.id === 'string' ? values.id.trim() : '';
    const projectId = rawId ? rawId.toLowerCase() : normalizeProjectId(name);

    if (!projectId) {
      message.error(t('projects.idRequired'));
      return;
    }
    if (!isValidProjectId(projectId)) {
      message.error(t('projects.invalidId'));
      return;
    }
    if (projects.some((project) => project.id === projectId)) {
      message.error(t('projects.duplicateId'));
      return;
    }

    const postgres = normalizePostgresPayload(values.postgres);
    const neo4j = normalizeNeo4jPayload(values.neo4j);

    if (
      !postgres?.host ||
      !postgres.user ||
      !postgres.database ||
      !postgres.password
    ) {
      message.error(t('projects.postgresRequired'));
      return;
    }

    if (!neo4j?.uri || !neo4j.user || !neo4j.password) {
      message.error(t('projects.neo4jRequired'));
      return;
    }

    const payload: ProjectConfigUpdatePayload = {
      postgres,
      neo4j,
    };

    try {
      await projectsApi.updateConfig(projectId, payload);
      addProject({ id: projectId, name: name || undefined });
      message.success(t('projects.created'));
      createForm.resetFields();
      setCreateOpen(false);
    } catch {
      message.error(t('projects.configSaveFailed'));
    }
  };

  const loadConfig = async () => {
    setConfigLoading(true);
    try {
      const config = await projectsApi.getConfig(currentProjectId);
      const postgres = config.postgres ?? null;
      const neo4j = config.neo4j ?? null;
      setPostgresHasPassword(Boolean(postgres?.has_password));
      setNeo4jHasPassword(Boolean(neo4j?.has_password));
      configForm.setFieldsValue({
        postgres: {
          host: postgres?.host ?? '',
          port: postgres?.port ?? 5432,
          user: postgres?.user ?? '',
          database: postgres?.database ?? '',
          sslmode: postgres?.sslmode ?? '',
          schema: postgres?.schema ?? '',
          password: '',
        },
        neo4j: {
          uri: neo4j?.uri ?? '',
          user: neo4j?.user ?? '',
          password: '',
        },
      });
    } catch {
      message.error(t('projects.configLoadFailed'));
    } finally {
      setConfigLoading(false);
    }
  };

  useEffect(() => {
    if (!configOpen) return;
    loadConfig();
  }, [configOpen, currentProjectId]);

  const handleConfigSave = async () => {
    let values: {
      postgres?: {
        host?: string;
        port?: number;
        user?: string;
        password?: string;
        database?: string;
        sslmode?: string;
        schema?: string;
      };
      neo4j?: { uri?: string; user?: string; password?: string };
    };
    try {
      values = await configForm.validateFields();
    } catch {
      return;
    }

    const payload: ProjectConfigUpdatePayload = {};

    payload.postgres = normalizePostgresPayload(values.postgres);
    payload.neo4j = normalizeNeo4jPayload(values.neo4j);

    const postgres = values.postgres || {};
    const postgresHasSecret = Boolean(postgres.password?.trim()) || postgresHasPassword;
    if (
      !postgres.host?.trim() ||
      !postgres.user?.trim() ||
      !postgres.database?.trim() ||
      !postgresHasSecret
    ) {
      message.error(t('projects.postgresRequired'));
      return;
    }

    const neo4j = values.neo4j || {};
    const neo4jHasSecret = Boolean(neo4j.password?.trim()) || neo4jHasPassword;
    if (!neo4j.uri?.trim() || !neo4j.user?.trim() || !neo4jHasSecret) {
      message.error(t('projects.neo4jRequired'));
      return;
    }

    try {
      await projectsApi.updateConfig(currentProjectId, payload);
      message.success(t('projects.configSaved'));
      setConfigOpen(false);
    } catch {
      message.error(t('projects.configSaveFailed'));
    }
  };

  return (
    <>
      <Space size={12}>
        <Select
          style={{ minWidth: 220 }}
          value={currentProjectId}
          options={options}
          onChange={(value) => setCurrentProjectId(value)}
        />
        <Button icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          {t('projects.new')}
        </Button>
        <Button icon={<SettingOutlined />} onClick={() => setConfigOpen(true)}>
          {t('projects.config')}
        </Button>
        <Popconfirm
          title={t('projects.deleteConfirm')}
          onConfirm={async () => {
            try {
              await projectsApi.deleteConfig(currentProjectId);
              removeProject(currentProjectId);
              message.success(t('projects.deleted'));
            } catch {
              message.error(t('projects.deleteFailed'));
            }
          }}
          okText={t('common.confirm')}
          cancelText={t('common.cancel')}
          disabled={currentProjectId === DEFAULT_PROJECT_ID}
        >
          <Button danger disabled={currentProjectId === DEFAULT_PROJECT_ID}>
            {t('projects.delete')}
          </Button>
        </Popconfirm>
      </Space>
      <Modal
        title={t('projects.new')}
        open={createOpen}
        onOk={handleCreate}
        onCancel={() => {
          createForm.resetFields();
          setCreateOpen(false);
        }}
        okText={t('projects.create')}
        cancelText={t('common.cancel')}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical">
          <Form.Item
            label={t('projects.name')}
            name="name"
            rules={[{ required: true, message: t('projects.nameRequired') }]}
          >
            <Input placeholder={t('projects.namePlaceholder')} />
          </Form.Item>
          <Form.Item
            label={t('projects.id')}
            name="id"
            extra={t('projects.idHint')}
          >
            <Input placeholder={t('projects.idPlaceholder')} />
          </Form.Item>
          <Divider orientation="left">{t('projects.postgresTitle')}</Divider>
          <Form.Item label={t('fields.host')} name={['postgres', 'host']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.port')} name={['postgres', 'port']}>
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label={t('fields.username')} name={['postgres', 'user']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.password')} name={['postgres', 'password']}>
            <Input.Password />
          </Form.Item>
          <Form.Item label={t('fields.database')} name={['postgres', 'database']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.schema')} name={['postgres', 'schema']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.sslmode')} name={['postgres', 'sslmode']}>
            <Input />
          </Form.Item>
          <Divider orientation="left">{t('projects.neo4jTitle')}</Divider>
          <Form.Item label={t('fields.uri')} name={['neo4j', 'uri']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.username')} name={['neo4j', 'user']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.password')} name={['neo4j', 'password']}>
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title={t('projects.config')}
        open={configOpen}
        onOk={handleConfigSave}
        onCancel={() => setConfigOpen(false)}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={configLoading}
        destroyOnClose
      >
        <Form form={configForm} layout="vertical">
          <Divider orientation="left">{t('projects.postgresTitle')}</Divider>
          <Form.Item label={t('fields.host')} name={['postgres', 'host']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.port')} name={['postgres', 'port']}>
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label={t('fields.username')} name={['postgres', 'user']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.password')} name={['postgres', 'password']}>
            <Input.Password />
          </Form.Item>
          <Form.Item label={t('fields.database')} name={['postgres', 'database']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.schema')} name={['postgres', 'schema']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.sslmode')} name={['postgres', 'sslmode']}>
            <Input />
          </Form.Item>
          <Divider orientation="left">{t('projects.neo4jTitle')}</Divider>
          <Form.Item label={t('fields.uri')} name={['neo4j', 'uri']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.username')} name={['neo4j', 'user']}>
            <Input />
          </Form.Item>
          <Form.Item label={t('fields.password')} name={['neo4j', 'password']}>
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default ProjectSwitcher;
