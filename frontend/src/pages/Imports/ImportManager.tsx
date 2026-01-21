import { useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Upload,
  message,
} from 'antd';
import type { UploadRequestOption } from 'rc-upload/lib/interface';
import { DeleteOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons';
import { useDeleteImportFile, useImportList, usePluginList, useUploadImport } from '@/hooks/useImports';
import type { PluginInfo } from '@/types/import';
import { useI18n } from '@/i18n';

const ImportManager = () => {
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [selectedPlugin, setSelectedPlugin] = useState<string>('auto');
  const { data: plugins = [], isLoading: pluginsLoading } = usePluginList();
  const { data, isLoading, refetch } = useImportList({ limit: 50, offset: 0 });
  const uploadMutation = useUploadImport();
  const deleteMutation = useDeleteImportFile();

  const pluginOptions = useMemo(() => {
    const options = [
      { label: t('common.autoDetect'), value: 'auto' },
      ...plugins.map((plugin) => ({
        label: `${plugin.name} (${plugin.version})`,
        value: plugin.name,
      })),
    ];
    return options;
  }, [plugins, t]);

  const selectedPluginInfo = useMemo<PluginInfo | undefined>(
    () => plugins.find((plugin) => plugin.name === selectedPlugin),
    [plugins, selectedPlugin],
  );

  const acceptTypes = useMemo(() => {
    if (!selectedPluginInfo) {
      return undefined;
    }
    const extensions = selectedPluginInfo.supported_formats
      .map((format) => format.trim().toLowerCase())
      .filter(Boolean)
      .map((format) => (format.startsWith('.') ? format : `.${format}`));
    return extensions.join(',');
  }, [selectedPluginInfo]);

  const handleUpload = async (options: UploadRequestOption) => {
    const { file, onSuccess, onError } = options;
    const values = form.getFieldsValue();
    try {
      await uploadMutation.mutateAsync({
        file: file as File,
        parserName: selectedPlugin === 'auto' ? undefined : selectedPlugin,
        createdBy: values.created_by || undefined,
      });
      onSuccess?.(null, file as File);
    } catch (error) {
      onError?.(error as Error);
    }
  };

  const validateBeforeUpload = (file: File) => {
    if (!selectedPluginInfo) {
      return true;
    }
    const allowed = selectedPluginInfo.supported_formats
      .map((format) => format.toLowerCase())
      .map((format) => (format.startsWith('.') ? format : `.${format}`));
    const suffix = `.${file.name.split('.').pop()?.toLowerCase()}`;
    if (allowed.length && !allowed.includes(suffix)) {
      message.error(
        `${t('imports.fileTypeError')}: ${allowed.join(', ')}`
      );
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  const statusTag = (status: string) => {
    if (status === 'SUCCESS') {
      return <Tag color="green">{status}</Tag>;
    }
    if (status === 'FAILED') {
      return <Tag color="red">{status}</Tag>;
    }
    if (status === 'PROCESSING') {
      return <Tag color="blue">{status}</Tag>;
    }
    if (status === 'DELETED') {
      return <Tag color="default">{status}</Tag>;
    }
    return <Tag>{status}</Tag>;
  };

  const columns = [
    {
      title: t('fields.name'),
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: t('fields.type'),
      dataIndex: 'format',
      key: 'format',
    },
    {
      title: t('fields.validationResult'),
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => statusTag(value),
    },
    {
      title: t('fields.validation'),
      key: 'records',
      render: (_: unknown, record: { records_success: number; records_failed: number }) =>
        `${record.records_success}/${record.records_failed}`,
    },
    {
      title: t('common.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: t('common.actions'),
      key: 'actions',
      render: (_: unknown, record: { id: string }) => (
        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={() => deleteMutation.mutate(record.id)}
        >
          {t('imports.deleteFile')}
        </Button>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title={t('imports.title')}>
        <Form form={form} layout="vertical" initialValues={{ created_by: '', parser_name: 'auto' }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label={t('imports.parser')} name="parser_name">
                <Select
                  options={pluginOptions}
                  loading={pluginsLoading}
                  value={selectedPlugin}
                  onChange={(value) => {
                    setSelectedPlugin(value);
                    form.setFieldsValue({ parser_name: value });
                  }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label={t('imports.createdBy')} name="created_by">
                <Input placeholder="scanner" />
              </Form.Item>
            </Col>
            <Col span={8} style={{ display: 'flex', alignItems: 'center' }}>
              <Upload
                accept={acceptTypes}
                beforeUpload={validateBeforeUpload}
                customRequest={handleUpload}
                showUploadList={false}
              >
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  loading={uploadMutation.isPending}
                >
                  {t('imports.upload')}
                </Button>
              </Upload>
            </Col>
          </Row>
        </Form>
      </Card>

      <Card
        title={t('imports.history')}
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            {t('common.refresh')}
          </Button>
        }
      >
        <Table
          rowKey="id"
          dataSource={data?.items || []}
          columns={columns}
          loading={isLoading}
          pagination={false}
        />
      </Card>
    </Space>
  );
};

export default ImportManager;
